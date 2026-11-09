set -eu
export DISPLAY=:0 XAUTHORITY=/run/asus-goodix/Xauthority
python3 - <<'PY'
from pathlib import Path
import json,subprocess,time,urllib.request
pid=json.loads(Path('/tmp/asus-osk-integration/state.json').read_text())['pid']
assert Path('/proc',str(pid),'cmdline').read_bytes().split(b'\0')[:2]==[b'/usr/bin/python3',b'/run/asus-goodix/osk-fixture-server.py']
owner=int(Path('/root/.mozilla/asus-appliance/lock').readlink().name.rsplit('+',1)[1])
windows=subprocess.check_output(['xdotool','search','--pid',str(owner),'--class','firefox'],text=True).split()
windows=[w for w in windows if '"Navigator"' in subprocess.check_output(['xprop','-id',w,'WM_CLASS'],text=True)]
assert windows
subprocess.run(['xdotool','windowactivate','--sync',windows[0]],check=True)
subprocess.run(['xdotool','key','ctrl+l'],check=True);time.sleep(.7)
subprocess.run(['xdotool','type','--clearmodifiers','--delay','40','http://127.0.0.1:8081/'],check=True)
time.sleep(.3);subprocess.run(['xdotool','key','Return'],check=True)
for i in range(100):
 d=json.load(urllib.request.urlopen('http://127.0.0.1:8081/state',timeout=.5))
 if d['fixture'] and d['fixture'].get('activeElement')=='entry' and d['fixture'].get('hasFocus'):break
 time.sleep(.1)
else:raise AssertionError('Fixture input still not focused')
print('REAL_FIXTURE_FOCUSED',json.dumps(d['fixture']))
PY
grep -E 'MemAvailable|SwapFree' /proc/meminfo
dmesg | grep -Ei 'out of memory|oom-killer|killed process' | tail -5 || true
