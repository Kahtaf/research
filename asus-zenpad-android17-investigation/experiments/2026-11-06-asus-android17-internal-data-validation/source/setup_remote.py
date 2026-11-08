from pathlib import Path
import shutil,hashlib,json,subprocess
R=Path('/srv/android/asus-internal-data-validation');B=Path('/srv/android/asus-android17-runtime-prereqs')
for n in ['source','inputs','evidence','artifacts','tests']: (R/n).mkdir()
# Explicit public runtime inputs only. No device/private artifacts.
items={'kernel':B/'build-r4/arch/arm64/boot/Image','payload-manifest.json':B/'handoff-r1/evidence/payload-manifest.json','guest_init.baseline.c':B/'handoff-r1/source/guest_init.c','analyze_materials.py':B/'handoff-r1/source/analyze_materials.py','adbd.apex':B/'inputs/adbd.apex','google.apex':B/'inputs/google.apex'}
pins=[]
for name,p in items.items():
 q=R/'inputs'/name;shutil.copyfile(p,q);h=hashlib.sha256(q.read_bytes()).hexdigest();assert h==hashlib.sha256(p.read_bytes()).hexdigest();q.chmod(0o444);pins.append(dict(source=str(p),copy=str(q),sha256=h,bytes=q.stat().st_size))
assert pins[0]['sha256']=='113c4f19c736b949626c62bbf68cf23c9e3c5a821ec6ab031a5684cdcba14431'
shutil.copytree(B/'inputs/root',R/'inputs/root')
for p in (R/'inputs/root').rglob('*'):
 if p.is_file():pins.append(dict(source=str(B/'inputs/root'/p.relative_to(R/'inputs/root')),copy=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size));p.chmod(0o444)
shutil.copyfile('/etc/mke2fs.conf',R/'inputs/mke2fs.conf')
for n in ['mke2fs','e2fsck','dumpe2fs','debugfs','qemu-system-aarch64','aarch64-linux-gnu-gcc','sha256sum']:
 p=Path(shutil.which(n));pins.append(dict(tool=n,path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
(R/'evidence/input-pins.json').write_text(json.dumps(pins,indent=2)+'\n')
print(json.dumps(pins[:6],indent=2))
