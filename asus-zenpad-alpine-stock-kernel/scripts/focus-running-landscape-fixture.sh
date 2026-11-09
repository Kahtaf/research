set -eu
export DISPLAY=:0 XAUTHORITY=/run/asus-goodix/Xauthority
python3 - <<'PY'
from pathlib import Path
import json,subprocess,time,urllib.request
run=Path('/run/asus-goodix/rotation-trial')
watch=json.loads((run/'state.json').read_text());assert watch['phase']=='ARMED'
assert Path('/proc',str(watch['pid']),'cmdline').read_bytes().endswith(b'/run/asus-goodix/rotation-trial/watchdog.py\0')
state=json.load(urllib.request.urlopen('http://127.0.0.1:8084/state',timeout=1))
assert Path('/proc',str(state['pid']),'cmdline').read_bytes().endswith(b'/run/asus-goodix/rotation-trial/fixture.py\0')
assert subprocess.check_output(['xdotool','getdisplaygeometry'],text=True).strip()=='1280 800'
subprocess.run(['python3','/usr/local/bin/goodix-open-url.py','http://127.0.0.1:8084/','--expect-title','ASUS landscape trial'],check=True)
for _ in range(100):
 state=json.load(urllib.request.urlopen('http://127.0.0.1:8084/state',timeout=1))
 if state['latest'] is not None:break
 time.sleep(.1)
else:raise AssertionError('Browser not ready')
x=state['latest']
assert x['screenWidth']>x['screenHeight'] and abs(x['screenWidth']/x['screenHeight']-1.6)<.02
(run/'READY').write_text('landscape-browser-ready-v1\n')
print('LANDSCAPE_BROWSER_READY',json.dumps(state['latest']))
print('SIX_MINUTE_PHYSICAL_WINDOW_STARTED')
PY
