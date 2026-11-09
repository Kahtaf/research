set -eu
python3 - <<'PY'
from pathlib import Path
import os,signal,stat
assert Path('/run/asus-alpine/root-mode').read_text().strip()=='SD-loop'
para=Path('/dev/mmcblk0p12');s=para.stat();assert stat.S_ISBLK(s.st_mode) and s.st_rdev==os.makedev(179,12)
with para.open('rb') as f:assert f.read(2048)==b'boot-recovery'+bytes(2048-len(b'boot-recovery'))
for entry in Path('/proc').iterdir():
 if not entry.name.isdecimal():continue
 try:args=(entry/'cmdline').read_bytes().split(b'\0')
 except (FileNotFoundError,ProcessLookupError):continue
 assert not (args and b'firefox' in args[0] and b'/root/.mozilla/asus-appliance' in args),'Close Firefox first'
for name,expected in [('dashboard.pid',b'/usr/local/bin/asus-dashboard.py'),('udhcpc.pid',b'udhcpc')]:
 p=int(Path('/run/asus-alpine',name).read_text());args=Path('/proc',str(p),'cmdline').read_bytes().split(b'\0')
 assert expected in args
 os.kill(p,signal.SIGTERM)
os.sync()
print('ORDINARY_LINUX_REBOOT; existing BCB command left untouched, no recovery argument',flush=True)
PY
sync
/sbin/reboot
