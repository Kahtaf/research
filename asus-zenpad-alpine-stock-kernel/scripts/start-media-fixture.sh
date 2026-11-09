set -eu
export DISPLAY=:0 XAUTHORITY=/run/asus-goodix/Xauthority
python3 - <<'PY'
from pathlib import Path
import json, subprocess, time, urllib.request
folder=Path('/tmp/asus-media-trial')
assert not (folder/'state.json').exists(), 'Refuse stale fixture directory'
with (folder/'server.log').open('ab') as log:
 server=subprocess.Popen(['python3',str(folder/'media-fixture.py')],stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
for _ in range(50):
 assert server.poll() is None
 try:urllib.request.urlopen('http://127.0.0.1:8083/state',timeout=.5);break
 except OSError:time.sleep(.1)
else:raise AssertionError('Fixture not listening')
lock=Path('/root/.mozilla/asus-appliance/lock')
owner=int(lock.readlink().name.rsplit('+',1)[1])
assert Path('/proc',str(owner),'cmdline').read_bytes().startswith(b'/usr/lib/firefox-esr/firefox-esr\0')
subprocess.run(['python3','/usr/local/bin/goodix-open-url.py','http://127.0.0.1:8083/','--expect-title','ASUS media trial'],check=True)
for _ in range(70):
 d=json.load(urllib.request.urlopen('http://127.0.0.1:8083/state',timeout=1))
 if any(e.get('event')=='ready' for e in d['events']):break
 time.sleep(.5)
else:raise AssertionError('No browser media result')
for e in d['events']:
 if e['event'] in ('loaded','error','play-rejected','ten-second-result','ready'):print(json.dumps(e))
PY
