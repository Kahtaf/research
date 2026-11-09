set -eu
python3 - <<'PY'
from pathlib import Path
import json,time
for directory,expected in (
 ('/tmp/asus-media-trial',b'/tmp/asus-media-trial/media-fixture.py\0'),
 ('/tmp/asus-landscape-trial',b'/run/asus-goodix/rotation-trial/fixture.py\0'),
):
 folder=Path(directory);state=json.loads((folder/'state.json').read_text());pid=state['pid']
 proc=Path('/proc',str(pid),'cmdline')
 if state['status']=='stopped':
  assert not proc.exists() or not proc.read_bytes().endswith(expected)
  print(directory,'already stopped');continue
 assert proc.read_bytes().endswith(expected), 'Unknown fixture owner'
 (folder/'STOP').touch()
 for _ in range(60):
  if not proc.exists():break
  time.sleep(.1)
 else:raise AssertionError('Owned fixture did not stop')
 assert json.loads((folder/'state.json').read_text())['status']=='stopped'
 print(directory,'stopped cleanly')
assert not Path('/usr/lib/firefox-esr/distribution/policies.json').exists()
assert not Path('/run/asus-goodix/rotation-trial/REQUEST').exists()
owner=int(Path('/root/.mozilla/asus-appliance/lock').readlink().name.rsplit('+',1)[1])
env=Path('/proc',str(owner),'environ').read_bytes().split(b'\0')
assert b'MOZ_USE_XINPUT2=1' in env
assert not any(field.startswith((b'MOZ_LOG=',b'MOZ_SANDBOX_LOGGING=')) for field in env)
print('NORMAL_FIREFOX_OWNER_LIVE',owner,'XI2 on, diagnostic logging off, rejected policy absent')
PY
amixer -c 0 cget name=Ext_Speaker_Amp_Switch
amixer -c 0 cget name=Speaker_Amp_Switch
