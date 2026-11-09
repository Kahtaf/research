set -eu
export DISPLAY=:0 XAUTHORITY=/run/asus-goodix/Xauthority
python3 - <<'PY'
from pathlib import Path
import os,signal,sqlite3,subprocess,time
profile=Path('/root/.mozilla/asus-appliance')
owner=int((profile/'lock').readlink().name.rsplit('+',1)[1]);original=Path('/proc',str(owner),'cmdline').read_bytes()
assert original.startswith(b'/usr/lib/firefox-esr/firefox-esr\0') and b'\0/root/.mozilla/asus-appliance\0' in original
env=os.environ.copy()
for field in Path('/proc',str(owner),'environ').read_bytes().split(b'\0'):
 if b'=' in field:
  key,value=field.split(b'=',1)
  if key.decode() in ('DBUS_SESSION_BUS_ADDRESS','GNOME_ACCESSIBILITY','GSETTINGS_BACKEND','XDG_RUNTIME_DIR','MOZ_USE_XINPUT2','LANG','HOME'):env[key.decode()]=value.decode()
windows=subprocess.check_output(['xdotool','search','--pid',str(owner),'--class','firefox'],text=True).split()
windows=[w for w in windows if '"Navigator"' in subprocess.check_output(['xprop','-id',w,'WM_CLASS'],text=True)]
for window in windows:subprocess.run(['xdotool','windowclose',window],check=True)
def alive():
 try:return Path('/proc',str(owner),'cmdline').read_bytes()==original
 except FileNotFoundError:return False
for _ in range(50):
 if not alive():break
 time.sleep(.1)
if alive():os.kill(owner,signal.SIGTERM)
for _ in range(50):
 if not alive():break
 time.sleep(.1)
else:raise AssertionError('Owned browser did not stop')
with sqlite3.connect('file:'+str(profile/'places.sqlite')+'?mode=ro',uri=True) as db:
 assert db.execute('PRAGMA quick_check').fetchone()[0]=='ok'
 print('CLOSED_PROFILE_QUICK_CHECK_OK; entries',db.execute('SELECT count(*) FROM moz_places').fetchone()[0])
for key in ('MOZ_LOG','MOZ_LOG_FILE','MOZ_SANDBOX_LOGGING'):env.pop(key,None)
env.update(ASUS_BROWSER='firefox-esr',ASUS_DASHBOARD_URL='http://127.0.0.1:8080/',ASUS_TOUCH_MODE='libinput',ASUS_OSK='onboard')
with Path('/run/asus-goodix/browser.log').open('ab') as log:
 child=subprocess.Popen(['/usr/local/bin/asus-goodix-browser'],env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
print('NORMAL_BROWSER_RESTARTED',child.pid)
PY
