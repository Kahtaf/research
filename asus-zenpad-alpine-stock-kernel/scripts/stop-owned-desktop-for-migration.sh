set -eu
export DISPLAY=:0 XAUTHORITY=/run/asus-goodix/Xauthority
p=$(cat /run/asus-goodix/desktop.pid)
python3 - <<'PY'
from pathlib import Path
import os,signal,sqlite3,subprocess,time
run=Path('/run/asus-goodix');controller=int((run/'desktop.pid').read_text())
args=Path('/proc',str(controller),'cmdline').read_bytes().split(b'\0')
assert any(b'asus-goodix-desktop' in x for x in args),args
profile=Path('/root/.mozilla/asus-appliance')
pid=int((profile/'lock').readlink().name.rsplit('+',1)[1]);args=Path('/proc',str(pid),'cmdline').read_bytes().split(b'\0')
assert b'/root/.mozilla/asus-appliance' in args,args
original=args
wins=subprocess.run(['xdotool','search','--onlyvisible','--pid',str(pid)],capture_output=True,text=True).stdout.split()
for win in wins:subprocess.run(['xdotool','windowclose',win],check=True)
def alive():
 try:return Path('/proc',str(pid),'cmdline').read_bytes().split(b'\0')==original
 except FileNotFoundError:return False
for i in range(50):
 if not alive():break
 time.sleep(.1)
if alive():
 # This legacy Firefox can retain its parent after the last X window closes.
 os.kill(pid,signal.SIGTERM)
 for i in range(50):
  if not alive():break
  time.sleep(.1)
 else:raise AssertionError('Browser did not stop after window close and TERM; no forced reboot')
os.kill(controller,15)
for i in range(50):
 if not Path('/proc',str(controller)).exists():break
 time.sleep(.1)
print('OWNED_FIREFOX_STOPPED; profile retained, no SIGKILL')
with sqlite3.connect('file:'+str(profile/'places.sqlite')+'?mode=ro',uri=True) as db:
 assert db.execute('PRAGMA quick_check').fetchone()[0]=='ok'
 count=db.execute('SELECT count(*) FROM moz_places').fetchone()[0]
 assert count>0
 print('CLOSED_BROWSER_HISTORY_INTEGRITY=ok RETAINED_ENTRIES='+str(count))
PY
sync
