set -eu
python3 - <<'PY'
from pathlib import Path
import json, os, subprocess, time
assert Path('/etc/asound.conf').read_text().startswith('# asus-alsa-rw-guard-v1\n')
assert Path('/proc/asound/card0/pcm0p/sub0/status').read_text().strip() == 'closed'
def amps_off():
    for name in ('Ext_Speaker_Amp_Switch','Speaker_Amp_Switch'):
        assert ': values=0' in subprocess.check_output(['amixer','-c','0','cget','name='+name],text=True)
amps_off()
for proc in Path('/proc').iterdir():
    if not proc.name.isdecimal(): continue
    try: args=(proc/'cmdline').read_bytes().split(b'\0')
    except FileNotFoundError: continue
    assert not (args and args[0] in (b'pulseaudio',b'/usr/bin/pulseaudio')), 'PulseAudio already exists'
run=Path('/run/asus-audio-trial');run.mkdir(mode=0o700)
runtime=Path('/run/user/0');runtime.mkdir(parents=True,mode=0o700,exist_ok=True)
assert not runtime.is_symlink() and runtime.stat().st_uid==0
runtime.chmod(0o700)
config=run/'pa-rw.pa'
config.write_text('.fail\nload-module module-alsa-sink device=hw:0,0 sink_name=asus_dl1_rw mmap=0 tsched=0 format=s16le rate=48000 channels=2\nload-module module-native-protocol-unix\nset-default-sink asus_dl1_rw\n')
env=dict(os.environ, XDG_RUNTIME_DIR=str(runtime))
with (run/'launcher.log').open('wb') as log:
    child=subprocess.Popen(['strace','-f','-tt','-yy','-e','trace=openat,mmap,ioctl','-o',str(run/'pa.strace'),'pulseaudio','-n','-F',str(config),'--daemonize=no','--exit-idle-time=-1','--disallow-exit','--disallow-module-loading','--use-pid-file=no','--realtime=no','--high-priority=no','--log-target=file:'+str(run/'pa.log'),'--log-level=info'],env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
try:
    for _ in range(80):
        assert child.poll() is None, 'Read PulseAudio trial logs'
        result=subprocess.run(['pactl','info'],env=env,capture_output=True,text=True)
        if result.returncode==0: break
        time.sleep(.1)
    else: raise AssertionError('PulseAudio not ready')
    children=[]
    for proc in Path('/proc').iterdir():
        if not proc.name.isdecimal(): continue
        try:
            if int((proc/'stat').read_text().rsplit(')',1)[1].split()[1])==child.pid and (proc/'exe').readlink()==Path('/usr/bin/pulseaudio'): children.append(int(proc.name))
        except FileNotFoundError: continue
    assert len(children)==1, children
    pid=children[0]
    stat=Path('/proc',str(pid),'stat').read_text().rsplit(')',1)[1].split()[19]
    params=Path('/proc/asound/card0/pcm0p/sub0/hw_params').read_text()
    assert 'access: RW_INTERLEAVED' in params and 'format: S16_LE' in params and 'rate: 48000' in params and 'channels: 2' in params,params
    maps=Path('/proc',str(pid),'maps').read_text()
    for line in maps.splitlines():
        if 'pcmC0D0p' in line: assert int(line.split()[2],16) in (0x80000000,0x81000000),line
    sinks=subprocess.check_output(['pactl','list','sinks'],env=env,text=True)
    assert 'device.access_mode = "serial"' in sinks,sinks
    log=(run/'pa.log').read_text();assert 'plug:' not in log,log
    amps_off()
    (run/'state.json').write_text(json.dumps({'pulse_pid':pid,'pulse_start':stat,'tracer_pid':child.pid,'hw_params':params,'phase':'SERIAL_SINK_READY'})+'\n')
    (run/'sinks.txt').write_text(sinks)
    print('PULSEAUDIO_RW_KERNEL_PARAMS_AND_SERIAL_SINK_PASS',pid)
    print(params)
except BaseException:
    # TERM only the exact traced child before failing. No mixer state is changed.
    for proc in Path('/proc').iterdir():
        if not proc.name.isdecimal(): continue
        try:
            if int((proc/'stat').read_text().rsplit(')',1)[1].split()[1])==child.pid and (proc/'exe').readlink()==Path('/usr/bin/pulseaudio'): os.kill(int(proc.name),15)
        except FileNotFoundError: pass
    raise
PY
