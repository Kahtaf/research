set -eu
python3 - <<'PY'
from pathlib import Path
import json,shutil,subprocess,time
folder=Path('/tmp/asus-media-trial');archive=Path('/tmp/asus-media-before-private-bundle')
assert not archive.exists() and not Path('/run/asus-goodix/rotation-trial/REQUEST').exists()
state=json.loads((folder/'state.json').read_text());assert state['status']=='stopped'
pid=Path('/proc',str(state['pid']),'cmdline')
assert not pid.exists() or not pid.read_bytes().endswith(b'/tmp/asus-media-trial/media-fixture.py\0')
folder.rename(archive);folder.mkdir(mode=0o700)
for name in ('media-video-only.mp4','media-with-audio.mp4','speaker-tone-trial.py'):
 shutil.copy2(archive/name,folder/name)
shutil.copy2('/tmp/asus-private-ffmpeg61-stage/media-fixture.py',folder/'media-fixture.py')
with (folder/'server.log').open('wb') as log:
 child=subprocess.Popen(['python3',str(folder/'media-fixture.py')],stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
for _ in range(40):
 assert child.poll() is None
 if (folder/'state.json').exists():break
 time.sleep(.1)
else:raise AssertionError('Fixture did not start')
state=json.loads((folder/'state.json').read_text());assert state['pid']==child.pid and not state['events']
print('FRESH_MEDIA_SERVER_READY_WITHOUT_BROWSER_NAVIGATION',child.pid)
PY
