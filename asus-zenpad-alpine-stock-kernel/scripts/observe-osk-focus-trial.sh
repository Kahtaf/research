set -eu
export DISPLAY=:0 XAUTHORITY=/run/asus-goodix/Xauthority
cat /tmp/asus-osk-trial/state.json
tail -15 /tmp/asus-osk-trial/onboard.log
tail -8 /tmp/asus-osk-trial/browser.log
python3 - <<'PY'
from pathlib import Path
import json,subprocess
d=json.loads(Path('/tmp/asus-osk-trial/state.json').read_text())
for key in ('onboard_pid','browser_pid'):
 p=d[key]
 r=subprocess.run(['xdotool','search','--pid',str(p)],capture_output=True,text=True)
 for w in r.stdout.split():
  subprocess.run(['xdotool','getwindowgeometry','--shell',w])
  subprocess.run(['xprop','-id',w,'WM_NAME','WM_CLASS','_NET_WM_WINDOW_TYPE','_NET_WM_STRUT_PARTIAL'])
PY
xprop -root _NET_WORKAREA
xwd -root -silent -out /tmp/asus-osk-trial/screen.xwd
