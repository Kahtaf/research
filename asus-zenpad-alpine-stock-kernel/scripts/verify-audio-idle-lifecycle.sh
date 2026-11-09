set -eu
export DISPLAY=:0 XAUTHORITY=/run/asus-goodix/Xauthority XDG_RUNTIME_DIR=/run/user/0
python3 - <<'PY'
from pathlib import Path
import json,os,subprocess,time,urllib.request
run=Path('/run/asus-audio-idle-trial');run.mkdir(mode=0o700)
state=json.loads(Path('/run/asus-goodix-audio/state.json').read_text());pid=state['pid']
assert Path('/proc',str(pid),'stat').read_text().rsplit(')',1)[1].split()[19]==state['start']
def amps_off():
 for n in ('Ext_Speaker_Amp_Switch','Speaker_Amp_Switch'):assert ': values=0' in subprocess.check_output(['amixer','-c','0','cget','name='+n],text=True)
def wait_idle():
 for _ in range(120):
  params=Path('/proc/asound/card0/pcm0p/sub0/hw_params').read_text().strip()
  if params=='closed':
   report=subprocess.check_output(['/usr/local/bin/asus-goodix-audio','status'],text=True)
   assert report.strip().endswith('SUSPENDED'),report
   for f in Path('/proc',str(pid),'fd').iterdir():
    try:target=str(f.readlink())
    except FileNotFoundError:continue
    assert '/dev/snd/pcm' not in target,target
   amps_off();return report.strip()
  time.sleep(.1)
 raise AssertionError('Audio did not release PCM on idle')
initial=wait_idle();print('INITIAL_IDLE',initial,flush=True)
assert not Path('/run/asus-browser-rw-audio').exists()
with (run/'fixture.log').open('wb') as log:
 server=subprocess.Popen(['python3','/tmp/asus-browser-rw-audio-fixture.py','--media','/tmp/asus-rw-media.mp4','--sha256','a232a648e0192e218ca6e2e3f06366c187c7bae052537b6eb7692d5ccceb2810'],stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
for _ in range(40):
 assert server.poll() is None
 try:urllib.request.urlopen('http://127.0.0.1:8087/state',timeout=.5);break
 except OSError:time.sleep(.1)
else:raise AssertionError('Fixture not ready')
try:
 subprocess.run(['python3','/usr/local/bin/goodix-open-url.py','http://127.0.0.1:8087/','--expect-title','ASUS browser audio routing check','--timeout','40'],check=True,timeout=43)
 for _ in range(70):
  events=json.load(urllib.request.urlopen('http://127.0.0.1:8087/state',timeout=1))['events']
  if any(e['event']=='ready' for e in events):break
  time.sleep(.1)
 else:raise AssertionError('No page readiness')
 subprocess.run(['xdotool','key','Return'],check=True)
 active=None;stream='';result=None
 for _ in range(120):
  events=json.load(urllib.request.urlopen('http://127.0.0.1:8087/state',timeout=1))['events']
  assert not any(e['event'] in ('error','play-rejected') for e in events),events
  params=Path('/proc/asound/card0/pcm0p/sub0/hw_params').read_text()
  if params.strip()!='closed' and any(e['event']=='playing' for e in events):
   for expected in ('access: RW_INTERLEAVED','format: S16_LE','rate: 48000','channels: 2'):assert expected in params,params
   if active is None:
    subprocess.run(['/usr/local/bin/asus-goodix-audio','status'],check=True)
    active=params
   if 'Firefox' not in stream:stream=subprocess.check_output(['pactl','list','sink-inputs'],text=True)
  result=next((e for e in events if e['event']=='result'),None)
  if result:break
  time.sleep(.2)
 assert result and result['time']>=9 and result['error'] is None and result['muted'] is False and result['volume']==.05,result
 assert active and 'Firefox' in stream
 for proc in Path('/proc').iterdir():
  if not proc.name.isdecimal():continue
  try:
   args=(proc/'cmdline').read_bytes().split(b'\0')
   if args and args[0]==b'/usr/lib/firefox-esr/firefox-esr':
    assert '/dev/snd/pcm' not in (proc/'maps').read_text()
    for f in (proc/'fd').iterdir():
     try:target=str(f.readlink())
     except FileNotFoundError:continue
     assert '/dev/snd/pcm' not in target,target
  except FileNotFoundError:continue
 amps_off()
 (run/'playback-events.json').write_text(json.dumps(events)+'\n')
 (run/'sink-inputs.txt').write_text(stream)
finally:
 subprocess.run(['python3','/usr/local/bin/goodix-open-url.py','http://127.0.0.1:8080/'],check=True,timeout=35)
 Path('/run/asus-browser-rw-audio/STOP').touch()
final=wait_idle()
assert Path('/proc',str(pid),'stat').read_text().rsplit(')',1)[1].split()[19]==state['start'],'Daemon unexpectedly restarted'
dmesg=subprocess.check_output(['dmesg'],text=True);assert 'Internal error: Oops' not in dmesg
receipt={'status':'IDLE_RESUME_IDLE_PASS','same_pulse_daemon':True,'initial_pcm':'closed','initial_sink':'SUSPENDED','active_hw_params':active,'playback_result':result,'final_pcm':'closed','final_sink':'SUSPENDED','idle_timeout_seconds':5,'amps_off_throughout':True,'firefox_hardware_pcm_fds':False,'new_kernel_oops':False}
(run/'result.json').write_text(json.dumps(receipt)+'\n');print('IDLE_AUDIO_RESULT',json.dumps(receipt),flush=True)
PY
