set -eu
export DISPLAY=:0 XAUTHORITY=/run/asus-goodix/Xauthority
python3 - <<'PY'
from pathlib import Path
import json,subprocess,time,urllib.request
run=Path('/run/asus-goodix/rotation-trial')
assert (run/'REQUEST').read_text()=='cw-v1\n'
for _ in range(100):
 r=subprocess.run(['xdotool','getdisplaygeometry'],capture_output=True,text=True)
 if r.returncode==0:break
 time.sleep(.1)
assert r.stdout.strip()=='1280 800',r.stdout
log=Path('/run/asus-goodix/Xorg.log').read_text()
assert 'rotating screen clockwise' in log.lower()
assert 'using shadow framebuffer' in log.lower()
classes=subprocess.check_output(['xinput','list','--long'],text=True)
assert 'XITouchClass' in classes and 'Max number of touches: 16' in classes
(run/'xinput.txt').write_text(classes)
for process in Path('/proc').iterdir():
 if not process.name.isdecimal():continue
 try:a=(process/'cmdline').read_bytes().split(b'\0')
 except FileNotFoundError:continue
 assert not (a and a[0].endswith(b'/z380m-touchbridge'))
for _ in range(100):
 lock=Path('/root/.mozilla/asus-appliance/lock')
 if lock.is_symlink():
  owner=int(lock.readlink().name.rsplit('+',1)[1])
  if Path('/proc',str(owner),'environ').exists():break
 time.sleep(.1)
else:raise AssertionError('No owned Firefox')
assert b'MOZ_USE_XINPUT2=1' in Path('/proc',str(owner),'environ').read_bytes().split(b'\0')
with (run/'fixture.log').open('ab') as output:
 server=subprocess.Popen(['python3',str(run/'fixture.py')],stdin=subprocess.DEVNULL,stdout=output,stderr=subprocess.STDOUT,start_new_session=True)
for _ in range(50):
 assert server.poll() is None
 try:urllib.request.urlopen('http://127.0.0.1:8084/state',timeout=.5);break
 except OSError:time.sleep(.1)
else:raise AssertionError('Fixture not listening')
subprocess.run(['python3','/usr/local/bin/goodix-open-url.py','http://127.0.0.1:8084/','--expect-title','ASUS landscape trial'],check=True)
for _ in range(100):
 d=json.load(urllib.request.urlopen('http://127.0.0.1:8084/state',timeout=.5))
 if d['latest'] is not None:break
 time.sleep(.1)
else:raise AssertionError('Browser did not load fixture')
x=d['latest']
assert x['screenWidth']>x['screenHeight'] and abs(x['screenWidth']/x['screenHeight']-1.6)<.02,x
watch=json.loads((run/'state.json').read_text());pid=watch['pid']
assert Path('/proc',str(pid),'cmdline').read_bytes().endswith(b'/run/asus-goodix/rotation-trial/watchdog.py\0')
assert watch['phase']=='ARMED'
(run/'READY').write_text('landscape-browser-ready-v1\n')
print('LANDSCAPE_BROWSER_READY',json.dumps(d['latest']))
print('PHYSICAL_WINDOW: six minutes from page readiness; RAM-only orientation')
PY
