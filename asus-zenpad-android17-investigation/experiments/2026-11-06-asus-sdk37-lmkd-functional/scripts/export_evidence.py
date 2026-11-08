from pathlib import Path
import json,hashlib,tarfile,datetime
R=Path('/srv/android/asus-sdk37-lmkd-functional');out=R/'exports';out.mkdir(exist_ok=True);selected=set()
def add(f):
 if f.is_file() and not f.is_symlink():selected.add(f)
for d in ['evidence','source','inputs/lmkd','inputs/native-r3']:
 for f in (R/d).rglob('*'):add(f)
for d in R.glob('run-*'):
 if d.is_dir():
  for f in d.iterdir():
   if f.suffix in ['.json','.log','.c','.py']:add(f)
for d in (R/'inputs').glob('fixture-*'):
 for f in d.iterdir():
  if f.suffix in ['.json','.log']:add(f)
 for p in ['fstab.mt8163','root/system/build.prop','root/system/etc/prop.default','root/system/etc/init/hw/init.rc','root/system/vendor/etc/fstab.memory','root/system/vendor/etc/selinux/vendor_file_contexts']:add(d/p)
for rev in ['native-r1','native-r2']:
 for f in (R/'inputs'/rev).iterdir():
  if f.suffix in ['.json','.readelf']:add(f)
K=R/'kernel-memory-r1'
for f in K.iterdir():
 if f.is_file():add(f)
for f in (K/'resume-r1').iterdir():add(f)
for p in ['out/.config','out/arch/arm64/boot/Image']:add(K/p)
manifest={str(f.relative_to(R)):{'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in sorted(selected)}
M=out/'manifest-r1.json';M.write_text(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':manifest,'total_bytes':sum(x['bytes'] for x in manifest.values())},indent=2))
with tarfile.open(out/'evidence-r1.tar.gz','w:gz') as a:
 for f in sorted(selected):a.add(f,arcname=str(f.relative_to(R)),recursive=False)
 a.add(M,arcname='export-manifest.json',recursive=False)
f=out/'evidence-r1.tar.gz';receipt={'files':len(manifest),'payload_bytes':sum(x['bytes'] for x in manifest.values()),'archive_bytes':f.stat().st_size,'archive_sha256':hashlib.sha256(f.read_bytes()).hexdigest()};(out/'receipt-r1.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt,indent=2))
