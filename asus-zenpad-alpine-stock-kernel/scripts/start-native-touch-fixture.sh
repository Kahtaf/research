set -eu
export DISPLAY=:0 XAUTHORITY=/run/asus-goodix/Xauthority
python3 - <<'PY'
from pathlib import Path
import json,subprocess,time,urllib.request
for i in range(100):
 r=subprocess.run(['xinput','list','--long'],capture_output=True,text=True)
 if r.returncode==0 and 'XITouchClass' in r.stdout:break
 time.sleep(.1)
classes=r.stdout
assert 'XITouchClass' in classes and 'Max number of touches: 16' in classes
Path('/run/asus-goodix/native-trial/xinput.txt').write_text(classes)
for p in Path('/proc').iterdir():
 if not p.name.isdecimal():continue
 try:a=(p/'cmdline').read_bytes().split(b'\0')
 except FileNotFoundError:continue
 assert not (a and a[0].endswith(b'/z380m-touchbridge')),'Legacy bridge still running'
for i in range(100):
 lock=Path('/root/.mozilla/asus-appliance/lock')
 if lock.is_symlink() and Path('/proc',lock.readlink().name.rsplit('+',1)[1]).exists():break
 time.sleep(.1)
owner=int(lock.readlink().name.rsplit('+',1)[1])
env=Path('/proc',str(owner),'environ').read_bytes().split(b'\0')
assert b'MOZ_USE_XINPUT2=1' in env
with Path('/run/asus-goodix/native-trial/fixture.log').open('ab') as log:
 server=subprocess.Popen(['/usr/bin/python3','/run/asus-goodix/native-trial/fixture.py'],stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
for i in range(50):
 assert server.poll() is None,'Fixture exited'
 try:urllib.request.urlopen('http://127.0.0.1:8082/state',timeout=.2);break
 except OSError:time.sleep(.1)
else:raise AssertionError('Fixture did not listen')
for i in range(100):
 result=subprocess.run(['xdotool','search','--pid',str(owner),'--class','firefox'],capture_output=True,text=True)
 windows=[w for w in result.stdout.split() if '"Navigator"' in subprocess.check_output(['xprop','-id',w,'WM_CLASS'],text=True)]
 if windows:break
 time.sleep(.1)
assert windows
for i in range(50):
 root=subprocess.run(['xprop','-root','_NET_ACTIVE_WINDOW'],capture_output=True,text=True).stdout
 if 'window id #' in root:break
 time.sleep(.1)
subprocess.run(['xdotool','windowactivate','--sync',windows[0]],check=True)
time.sleep(.5)
subprocess.run(['xdotool','key','ctrl+l'],check=True);time.sleep(1)
subprocess.run(['xdotool','type','--clearmodifiers','--delay','40','http://127.0.0.1:8082/'],check=True)
time.sleep(.3);subprocess.run(['xdotool','key','Return'],check=True)
for i in range(100):
 d=json.load(urllib.request.urlopen('http://127.0.0.1:8082/state',timeout=.5))
 if d['latest'] is not None:break
 time.sleep(.1)
else:raise AssertionError('Browser did not load fixture')
print('NATIVE_BROWSER_READY',json.dumps(d['latest']))
# ESR140's GTK base widget reports maxTouchPoints=0 even for XI2 touch devices.
# Device classes and actual touch/scroll events are the qualification gates.
watch=json.loads(Path('/run/asus-goodix/native-trial/state.json').read_text())
assert Path('/proc',str(watch['pid']),'cmdline').exists()
assert watch['phase']=='ARMED'
Path('/run/asus-goodix/native-trial/READY').write_text('native-browser-ready-v1\n')
print('PHYSICAL_CHECK_WINDOW_STARTED; six minutes after page readiness')
PY
