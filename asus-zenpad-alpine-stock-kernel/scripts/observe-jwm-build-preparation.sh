set -eu
python3 - <<'PY'
from pathlib import Path
for p in Path('/proc').iterdir():
 if not p.name.isdecimal():continue
 try:args=(p/'cmdline').read_bytes().split(b'\0')
 except (FileNotFoundError,ProcessLookupError):continue
 if args and args[0] and Path(args[0].decode()).name in ('apk','cc1','gcc','make','cc'):
  print('BUILD_PREPARATION_PROCESS',p.name,b' '.join(args[:5]).decode())
  print((p/'stat').read_text().split(') ',1)[1].split()[:3])
PY
df -h /
