export DISPLAY=:0 XAUTHORITY=/run/asus-goodix/Xauthority
xdotool search --onlyvisible --name . getwindowname
python3 - <<'PY'
from pathlib import Path
for p in Path('/proc').iterdir():
 if not p.name.isdecimal():continue
 try:args=(p/'cmdline').read_bytes().split(b'\0')
 except (FileNotFoundError,ProcessLookupError):continue
 if args and b'firefox' in args[0] and b'/root/.mozilla/asus-appliance' in args:
  print('PROFILE_PARENT',p.name,'ARGS',b' '.join(args).decode())
  print((p/'status').read_text().split('VmPeak')[0])
PY
