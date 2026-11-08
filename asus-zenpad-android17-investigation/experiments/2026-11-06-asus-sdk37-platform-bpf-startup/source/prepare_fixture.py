from pathlib import Path
import os,hashlib,json,shutil,subprocess as s
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
R=Path('/srv/android/asus-network-runtime');O=Path('/srv/android/asus-sdk37-platform-bpf-startup-20261106');D=O/'inputs/runtime-root';D.mkdir(exist_ok=False)
manifest={}
def cp(src,dest):
 dest.parent.mkdir(parents=True,exist_ok=True);h=hashlib.sha256(src.read_bytes()).hexdigest();shutil.copyfile(src,dest);assert h==hashlib.sha256(src.read_bytes()).hexdigest()==hashlib.sha256(dest.read_bytes()).hexdigest();manifest[str(dest.relative_to(O))]={'source':str(src),'sha256':h,'bytes':dest.stat().st_size}
for base in [R/'inputs/root',R/'inputs/platform-root']:
 for p in base.rglob('*'):
  if p.is_file():cp(p,D/p.relative_to(base))
for p in (R/'artifacts/bpf-original').glob('*.o'):
 if '.unstripped.' not in p.name:cp(p,D/'apex/com.android.tethering/etc/bpf/mainline'/p.name)
cp(R/'handoff-r1/netd.o',D/'apex/com.android.tethering/etc/bpf/mainline/netd.o')
cp(R/'handoff-r1/netbpfload',D/'system/bin/network_loader');cp(R/'handoff-r1/netbpfload',D/'apex/com.android.tethering/bin/netbpfload')
cp(R/'artifacts/seed_properties',D/'system/bin/seed_properties')
cp(R/'handoff-r1/Image',O/'inputs/network-qualified.Image')
# Capture the complete selected graph inventory, while retaining reviewed Connectivity patch11 object.
for p in (O/'inputs/selected-root').rglob('*'):
 if p.is_file() and str(p.relative_to(O/'inputs/selected-root')) != 'apex/com.android.tethering/etc/bpf/mainline/netd.o':
  rel=p.relative_to(O/'inputs/selected-root')
  if str(rel).startswith('apex/com.android.tethering/') and (D/rel).exists():assert hashlib.sha256(p.read_bytes()).digest()==hashlib.sha256((D/rel).read_bytes()).digest(),rel
  cp(p,D/rel)
(O/'evidence/runtime-capture.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Runtime files',len(manifest),'bytes',sum(x['bytes'] for x in manifest.values()))
