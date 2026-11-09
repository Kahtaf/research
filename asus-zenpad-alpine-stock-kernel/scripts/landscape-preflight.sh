set -eu
python3 - <<'PY'
from pathlib import Path
import hashlib,json,subprocess
assert Path('/etc/asus-goodix/native-touch').read_text()=='libinput-v1\n'
assert not Path('/etc/asus-goodix/rotation').exists()
assert not Path('/run/asus-goodix/rotation-trial').exists()
assert not Path('/tmp/asus-landscape-trial').exists()
for name in ('Ext_Speaker_Amp_Switch','Speaker_Amp_Switch'):
 text=subprocess.check_output(['amixer','-c','0','cget','name='+name],text=True)
 assert ': values=0' in text
assert Path('/proc/asound/card0/pcm0p/sub0/status').read_text().strip()=='closed'
for name in ('/usr/local/bin/asus-goodix-desktop','/etc/asus-alpine/start-desktop','/etc/X11/asus-goodix-libinput.conf'):
 p=Path(name);print(name,'SHA256',hashlib.sha256(p.read_bytes()).hexdigest());print(p.read_text())
pid=int(Path('/run/asus-goodix/desktop.pid').read_text())
assert b'asus-goodix-desktop' in Path('/proc',str(pid),'cmdline').read_bytes()
print('DESKTOP_CONTROLLER_LIVE',pid)
PY
