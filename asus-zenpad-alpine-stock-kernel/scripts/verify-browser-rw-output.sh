set -eu
export DISPLAY=:0 XAUTHORITY=/run/asus-goodix/Xauthority XDG_RUNTIME_DIR=/run/user/0
python3 - <<'PY'
from pathlib import Path
import hashlib,json,os,subprocess,time,urllib.request
amps=('Ext_Speaker_Amp_Switch','Speaker_Amp_Switch')
def amps_off():
 for name in amps:assert ': values=0' in subprocess.check_output(['amixer','-c','0','cget','name='+name],text=True)
amps_off()
assert 'access: RW_INTERLEAVED' in Path('/proc/asound/card0/pcm0p/sub0/hw_params').read_text()
assert not Path('/run/asus-browser-rw-audio').exists()
with Path('/run/asus-audio-trial/fixture.log').open('wb') as log:
 server=subprocess.Popen(['python3','/tmp/asus-browser-rw-audio-fixture.py','--media','/tmp/asus-rw-media.mp4','--sha256','a232a648e0192e218ca6e2e3f06366c187c7bae052537b6eb7692d5ccceb2810'],stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
for _ in range(40):
 assert server.poll() is None
 try:urllib.request.urlopen('http://127.0.0.1:8087/state',timeout=.5);break
 except OSError:time.sleep(.1)
else:raise AssertionError('Fixture not listening')
subprocess.run(['python3','/usr/local/bin/goodix-open-url.py','http://127.0.0.1:8087/','--expect-title','ASUS browser audio routing check','--timeout','40'],check=True,timeout=43)
for _ in range(70):
 state=json.load(urllib.request.urlopen('http://127.0.0.1:8087/state',timeout=1))
 if any(e['event']=='ready' for e in state['events']):break
 time.sleep(.1)
else:raise AssertionError('No fixture readiness')
subprocess.run(['xdotool','key','Return'],check=True)
stream=None
for _ in range(110):
 state=json.load(urllib.request.urlopen('http://127.0.0.1:8087/state',timeout=1))
 if (not stream or 'Firefox' not in stream) and any(e['event']=='playing' for e in state['events']):
  stream=subprocess.check_output(['pactl','list','sink-inputs'],text=True)
 if any(e['event'] in ('result','error','play-rejected') for e in state['events']):break
 time.sleep(.2)
(run:=Path('/run/asus-audio-trial')).joinpath('browser-state.json').write_text(json.dumps(state)+'\n')
(run/'browser-sink-inputs.txt').write_text(stream or '')
print('BROWSER_EVENTS',json.dumps(state))
assert any(e['event']=='trusted-play' for e in state['events'])
result=next(e for e in state['events'] if e['event']=='result')
assert result['time']>=9 and result['error'] is None and result['muted'] is False and result['volume']==.05,result
assert stream and 'Firefox' in stream,stream
pulse_mapped=[];utility=[];count=0
for proc in Path('/proc').iterdir():
 if not proc.name.isdecimal():continue
 try:
  args=(proc/'cmdline').read_bytes().split(b'\0')
  if not args or args[0]!=b'/usr/lib/firefox-esr/firefox-esr':continue
  count+=1;maps=(proc/'maps').read_text()
  assert '/dev/snd/pcm' not in maps,proc
  for f in (proc/'fd').iterdir():
   try:target=str(f.readlink())
   except FileNotFoundError:continue
   assert '/dev/snd/pcm' not in target,(proc,target)
  if 'libpulse.so.0' in maps:pulse_mapped.append(int(proc.name))
  if b'utility' in args or b'-utility' in args:
   status=(proc/'status').read_text();assert 'Seccomp:\t2' in status
   utility.append(int(proc.name))
 except FileNotFoundError:continue
assert pulse_mapped and utility, (pulse_mapped,utility)
params=Path('/proc/asound/card0/pcm0p/sub0/hw_params').read_text()
assert 'access: RW_INTERLEAVED' in params
amps_off()
dmesg=subprocess.check_output(['dmesg'],text=True)
assert 'Unable to handle kernel paging request' not in dmesg and 'Internal error: Oops' not in dmesg
receipt={'result':result,'firefox_processes_checked':count,'pulse_library_pids':pulse_mapped,'sandboxed_utility_pids':utility,'firefox_hardware_pcm_fds':False,'hardware_access':'RW_INTERLEAVED','amps_off':True,'new_kernel_oops':False}
(run/'browser-result.json').write_text(json.dumps(receipt)+'\n')
print('STEP_B_UNMUTED_BROWSER_SERIAL_OUTPUT_PASS',json.dumps(receipt))
subprocess.run(['python3','/usr/local/bin/goodix-open-url.py','http://127.0.0.1:8080/'],check=True)
Path('/run/asus-browser-rw-audio/STOP').touch()
PY
