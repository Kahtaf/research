set -eu
python3 - <<'PY'
from pathlib import Path
import hashlib,os,signal,stat,subprocess,time
assert Path('/run/asus-alpine/root-mode').read_text().strip()=='SD-loop'
def node(part,start,sectors):
 s=Path('/sys/class/block',part)
 assert int((s/'start').read_text())==start and int((s/'size').read_text())==sectors
 major,minor=map(int,(s/'dev').read_text().split(':'))
 p=Path('/dev',part);d=p.stat();assert stat.S_ISBLK(d.st_mode) and d.st_rdev==os.makedev(major,minor)
 return p
boot=node('mmcblk0p9',127488,32696)
assert hashlib.sha256(boot.read_bytes()).hexdigest()=='7bb68511b1ade34d24c3e932da7260e6753fa87270bd8249a7218755a5df3316'
para=node('mmcblk0p12',225576,1024)
with para.open('rb') as f:bcb=f.read(2048)
assert not any(bcb),'Stock return requires the already-clean empty BCB'
assert Path('/root/asus-first-sd-boot.txt').is_file()
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
print('STOCK_RETURN_PRECONDITIONS_PASS; stock BOOT, empty BCB, OS/browser data synced',flush=True)
PY
sync
/sbin/reboot
