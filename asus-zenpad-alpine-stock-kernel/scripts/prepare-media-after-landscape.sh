set -eu
export DISPLAY=:0 XAUTHORITY=/run/asus-goodix/Xauthority
python3 - <<'PY'
from pathlib import Path
import json,shutil,subprocess
run=Path('/run/asus-goodix/rotation-trial')
watch=json.loads((run/'state.json').read_text())
assert watch['phase']=='RESTORED_NATIVE_PORTRAIT',watch
assert not (run/'REQUEST').exists() and not Path('/etc/asus-goodix/rotation').exists()
assert subprocess.check_output(['xdotool','getdisplaygeometry'],text=True).strip()=='800 1280'
assert 'Max number of touches: 16' in subprocess.check_output(['xinput','list','--long'],text=True)
folder=Path('/tmp/asus-media-trial');archive=Path('/tmp/asus-media-first-pass')
assert not archive.exists()
state=json.loads((folder/'state.json').read_text());assert state['status']=='stopped'
assert not Path('/proc',str(state['pid'])).exists(), 'Old fixture PID still exists'
folder.rename(archive);folder.mkdir(mode=0o700)
for name in ('media-video-only.mp4','media-with-audio.mp4','speaker-tone-trial.py'):
 shutil.copy2(archive/name,folder/name)
print('NATIVE_PORTRAIT_RESTORED; original media evidence archived, fresh fixture directory prepared')
PY
