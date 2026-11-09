set -eu
export DISPLAY=:0 XAUTHORITY=/run/asus-goodix/Xauthority
xdotool search --onlyvisible --name . getwindowname
tail -35 /run/asus-goodix/browser.log
python3 - <<'PY'
from pathlib import Path
for p in Path('/proc').iterdir():
 if not p.name.isdecimal():continue
 try:args=(p/'cmdline').read_bytes().split(b'\0')
 except (FileNotFoundError,ProcessLookupError):continue
 if args and args[0] and b'firefox' in args[0]:print(p.name,b' '.join(args[:4]).decode(errors='replace'))
profile=Path('/root/.mozilla/asus-appliance')
for n in ('lock','.parentlock'):
 p=profile/n
 print('PROFILE_LOCK',n,'symlink',p.is_symlink(),'target',p.readlink() if p.is_symlink() else 'regular' if p.exists() else 'absent')
PY
xwd -root -silent -out /tmp/sd-desktop.xwd
