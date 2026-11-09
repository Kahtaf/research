set -eu
export DISPLAY=:0 XAUTHORITY=/run/asus-goodix/Xauthority
python3 - <<'PY'
from pathlib import Path
import json,time
run=Path('/run/asus-goodix/rotation-trial');watch=json.loads((run/'state.json').read_text())
process=Path('/proc',str(watch['pid']),'cmdline')
watch['owned_pid_live']=process.exists() and process.read_bytes().endswith(b'/run/asus-goodix/rotation-trial/watchdog.py\0')
watch['remaining_seconds']=round(watch['deadline_monotonic']-time.monotonic())
print('WATCHDOG',json.dumps(watch))
data=json.loads(Path('/tmp/asus-landscape-trial/state.json').read_text())
print('LATEST',json.dumps(data['latest']))
events=data['events']
print('PROGRESS',json.dumps({'corner_hits':sorted({h for e in events for h in e['cornerHits']}),'max_contacts':max([e['maxTouches'] for e in events],default=0),'max_scroll_y':max([e['scrollY'] for e in events],default=0),'max_scale':max([e['scale'] for e in events],default=1),'typed_ok':any(e['value']=='ok' for e in events),'done_after_ok':any(e['reason']=='done-click' and e['value']=='ok' for e in events)}))
PY
xdotool getdisplaygeometry
