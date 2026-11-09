set -eu
export DISPLAY=:0 XAUTHORITY=/run/asus-goodix/Xauthority
python3 - <<'PY'
from pathlib import Path
import json,subprocess,time,urllib.request
script=Path('/tmp/asus-youtube-workload.py')
folder=Path('/tmp/asus-youtube-workload')
existing=False
if folder.exists():
 d=json.loads((folder/'state.json').read_text());proc=Path('/proc',str(d['pid']),'cmdline')
 if d['status']=='running':
  assert proc.exists() and proc.read_bytes().endswith(b'/tmp/asus-youtube-workload.py\0')
  existing=True
 else:
  assert d['status']=='stopped' and (not proc.exists() or not proc.read_bytes().endswith(b'/tmp/asus-youtube-workload.py\0'))
  archive=Path('/tmp/asus-youtube-workload-before-navigation');assert not archive.exists();folder.rename(archive)
if not existing:
 with Path('/tmp/asus-youtube-workload.log').open('ab') as log:
  server=subprocess.Popen(['python3',str(script)],stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 for _ in range(40):
  assert server.poll() is None
  try:urllib.request.urlopen('http://127.0.0.1:8086/state',timeout=.5);break
  except OSError:time.sleep(.1)
 else:raise AssertionError('Observer not listening')
subprocess.run(['python3','/usr/local/bin/goodix-open-url.py','http://127.0.0.1:8086/','--expect-title','ASUS YouTube workload'],check=True)
for _ in range(100):
 state=json.load(urllib.request.urlopen('http://127.0.0.1:8086/state',timeout=1))
 if any(e['kind'] in ('ready','player-error','api-load-error') for e in state['events']):break
 time.sleep(.4)
else:raise AssertionError('Player did not become ready')
print('PLAYER_READY_STATE',json.dumps(state['latest']))
if any(e['kind']=='ready' for e in state['events']):
 subprocess.run(['xdotool','key','Return'],check=True)
 for _ in range(80):
  state=json.load(urllib.request.urlopen('http://127.0.0.1:8086/state',timeout=1))
  if any(e['kind'] in ('complete','player-error') for e in state['events']):break
  time.sleep(.4)
for e in state['events']:
 if e['kind'] in ('ready','trusted-play','player-error','api-load-error','autoplay-blocked','complete'):print(json.dumps(e))
print('MAX_YOUTUBE_SECONDS',max((e.get('playbackTime',0) for e in state['events']),default=0))
PY
