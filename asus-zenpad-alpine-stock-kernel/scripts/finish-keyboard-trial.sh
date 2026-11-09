set -eu
export DISPLAY=:0 XAUTHORITY=/run/asus-goodix/Xauthority
python3 - <<'PY'
from pathlib import Path
import json,os,subprocess,time,urllib.request
result=json.loads(Path('/tmp/asus-osk-integration/state.json').read_text())
assert any(e.get('value')=='tablet' for e in result['events'])
windows=subprocess.run(['xdotool','search','--name','ASUS automatic keyboard trial.*Mozilla Firefox'],capture_output=True,text=True).stdout.split()
if windows:
 assert len(windows)==1
 subprocess.run(['xdotool','windowactivate','--sync',windows[0]],check=True)
 subprocess.run(['xdotool','key','ctrl+l'],check=True);time.sleep(.7)
 subprocess.run(['xdotool','type','--clearmodifiers','--delay','40','http://127.0.0.1:8080/'],check=True)
 time.sleep(.3);subprocess.run(['xdotool','key','Return'],check=True)
 for i in range(100):
  title=subprocess.check_output(['xdotool','getwindowname',windows[0]],text=True)
  if 'ASUS Alpine dashboard' in title:break
  time.sleep(.1)
 else:raise AssertionError('Dashboard did not return')
 print('OWNER_BROWSER_RETURNED_TO_DASHBOARD')
else:print('OWNER_CHANGED_BROWSER_PAGE; left their page intact')
Path('/tmp/asus-osk-integration/STOP').touch()
health=json.load(urllib.request.urlopen('http://127.0.0.1:8080/health',timeout=3))
print('DASHBOARD_SAVED_REQUESTS',health['requests_saved'])
pid=int(Path('/run/asus-goodix/onboard.pid').read_text())
env=dict(v.split(b'=',1) for v in Path('/proc',str(pid),'environ').read_bytes().split(b'\0') if b'=' in v)
os.environ['DBUS_SESSION_BUS_ADDRESS']=env[b'DBUS_SESSION_BUS_ADDRESS'].decode()
import dbus
keyboard=dbus.SessionBus().get_object('org.onboard.Onboard','/org/onboard/Onboard/Keyboard')
dbus.Interface(keyboard,'org.onboard.Onboard.Keyboard').Hide()
print('AUTOMATIC_KEYBOARD_LEFT_RUNNING; normal focus will show it')
os.sync()
PY
