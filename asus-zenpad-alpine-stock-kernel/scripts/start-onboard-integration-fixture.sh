set -eu
export DISPLAY=:0 XAUTHORITY=/run/asus-goodix/Xauthority
python3 - <<'PY'
from pathlib import Path
import os,subprocess,time,urllib.request
log=Path('/run/asus-goodix/osk-fixture.log').open('ab')
server=subprocess.Popen(['/usr/bin/python3','/run/asus-goodix/osk-fixture-server.py'],stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
Path('/run/asus-goodix/osk-fixture.pid').write_text(str(server.pid)+'\n')
for i in range(50):
 assert server.poll() is None,'Fixture exited; inspect log'
 try:urllib.request.urlopen('http://127.0.0.1:8081/state',timeout=.2);break
 except OSError:time.sleep(.1)
else:raise AssertionError('Fixture did not listen')
for i in range(100):
 lock=Path('/root/.mozilla/asus-appliance/lock')
 if lock.is_symlink():
  owner=int(lock.readlink().name.rsplit('+',1)[1])
  result=subprocess.run(['xdotool','search','--pid',str(owner),'--class','firefox'],capture_output=True,text=True)
  windows=[]
  for w in result.stdout.split():
   if '_NET_WM_WINDOW_TYPE_NORMAL' in subprocess.check_output(['xprop','-id',w,'_NET_WM_WINDOW_TYPE'],text=True):windows.append(w)
  if windows:break
 time.sleep(.1)
else:raise AssertionError('No owner Firefox normal window')
subprocess.run(['xdotool','windowactivate',windows[0],'key','ctrl+l','type','--clearmodifiers','http://127.0.0.1:8081/'],check=True)
subprocess.run(['xdotool','key','Return'],check=True)
for i in range(100):
 import json
 state=json.load(urllib.request.urlopen('http://127.0.0.1:8081/state',timeout=.5))
 if state['fixture'] and state['fixture'].get('activeElement')=='entry' and state['fixture'].get('hasFocus'):break
 time.sleep(.1)
else:raise AssertionError('Browser fixture input not focused')
print('OWNER_BROWSER_FIXTURE_FOCUSED; existing profile retained')
PY
