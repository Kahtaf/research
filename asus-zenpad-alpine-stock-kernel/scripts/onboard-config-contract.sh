set -eu
gsettings list-keys org.onboard.window.portrait
gsettings list-keys org.onboard.window.landscape
sed -n '895,966p' /usr/lib/python*/site-packages/Onboard/OnboardGtk.py
cat /tmp/asus-osk-trial/typing-proof.json
python3 - <<'PY'
from pathlib import Path
import json
d=json.loads(Path('/tmp/asus-osk-trial/state.json').read_text())
assert d['status']=='stopped',d
assert d['browser_exit_code'] is not None and d['onboard_exit_code'] is not None
print('ISOLATED_TRIAL_TERMINAL_CLEAN; original Firefox profile not used')
PY
jwm -v
