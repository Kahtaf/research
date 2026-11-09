set -eu
python3 - <<'PY'
from pathlib import Path
import shutil
p=Path('/tmp/firefox-modern-proof')
assert p.is_dir() and not p.is_symlink()
for item in Path('/proc').iterdir():
 if not item.name.isdecimal():continue
 try:args=(item/'cmdline').read_bytes().split(b'\0')
 except (FileNotFoundError,ProcessLookupError):continue
 assert b'/tmp/firefox-modern-proof' not in args,'Headless proof process still uses its profile'
shutil.rmtree(p)
for name in ('/tmp/firefox-modern-visible.xwd','/tmp/standalone-desktop.xwd','/tmp/firefox-https.png'):
 f=Path(name)
 if f.exists():
  assert f.is_file() and not f.is_symlink();f.unlink()
print('OWNED_HEADLESS_TEST_FILES_REMOVED; interactive Firefox profile preserved')
PY
df -h /
