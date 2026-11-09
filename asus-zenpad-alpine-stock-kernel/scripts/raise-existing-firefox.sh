set -eu
export DISPLAY=:0 XAUTHORITY=/run/asus-goodix/Xauthority ASUS_BROWSER=firefox-esr
python3 - <<'PY'
from pathlib import Path
import subprocess,time
profile=Path('/root/.mozilla/asus-appliance')
owner=int((profile/'lock').readlink().name.rsplit('+',1)[1])
out=subprocess.run(['xdotool','search','--onlyvisible','--name','^Close Firefox$'],capture_output=True,text=True)
for win in out.stdout.split():
 pid=int(subprocess.check_output(['xdotool','getwindowpid',win],text=True))
 assert pid!=owner
 args=Path('/proc',str(pid),'cmdline').read_bytes().split(b'\0')
 assert b'/root/.mozilla/asus-appliance' in args and Path(args[0].decode()).name=='firefox-esr'
 subprocess.run(['xdotool','windowclose',win],check=True)
 time.sleep(.2)
subprocess.run(['/usr/local/bin/asus-goodix-browser'],check=True)
assert int((profile/'lock').readlink().name.rsplit('+',1)[1])==owner
print('BROWSER_MENU_RAISES_SAME_PROFILE_OWNER; profile retained')
PY
xdotool search --onlyvisible --class firefox getwindowname
