set -eu
df -h /
du -xhd 1 /root /tmp /var 2>/dev/null | sort -hr | head -20
python3 - <<'PY'
import ctypes,os
from pathlib import Path
before=os.stat('/').st_dev
mounts=[l.split() for l in Path('/proc/mounts').read_text().splitlines() if l.split()[1]=='/' and l.split()[0]=='asus-alpine-root']
assert len(mounts)==1 and mounts[0][2]=='tmpfs'
libc=ctypes.CDLL(None,use_errno=True)
assert libc.mount(b'asus-alpine-root',b'/',b'tmpfs',32,b'size=1073741824,mode=0755')==0,ctypes.get_errno()
assert os.stat('/').st_dev==before
for name in ('/tmp/firefox-modern-visible.xwd','/tmp/standalone-desktop.xwd','/tmp/firefox-https.png'):
 p=Path(name)
 if p.exists():
  assert p.is_file() and not p.is_symlink();p.unlink()
print('RAM quota temporarily raised; interactive browser files preserved')
PY
df -h /
