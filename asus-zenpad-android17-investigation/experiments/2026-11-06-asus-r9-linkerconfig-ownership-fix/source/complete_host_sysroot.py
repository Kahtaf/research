from pathlib import Path
import os,json,hashlib,shutil
R=Path('/srv/android/asus-r9-linkerconfig-ownership-fix-20261106');A=Path('/srv/android/lineage24');S=R/'inputs/native-snapshot';os.environ['TMPDIR']=str(R/'tmp');base='prebuilts/gcc/linux-x86/host/x86_64-linux-glibc2.17-4.8';roots=[base+'/sysroot/usr/lib',base+'/sysroot/usr/lib64',base+'/sysroot/lib',base+'/sysroot/lib64',base+'/lib/gcc/x86_64-linux/4.8',base+'/lib64/gcc/x86_64-linux/4.8',base+'/x86_64-linux/lib64'];pins={}
files=[]
for n in roots:
 p=A/n
 if p.is_dir():files += [f for f in p.rglob('*') if f.is_file()]
assert sum(p.stat().st_size for p in files)<80*1024**2
for p in files:
 rel=str(p.relative_to(A));b=p.read_bytes();dest=S/rel;dest.parent.mkdir(exist_ok=True,parents=True);dest.write_bytes(b);pins[rel]={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
(R/'evidence/host-sysroot-extra-pins.json').write_text(json.dumps(pins,indent=2));(R/'evidence/native-build-failure1.json').write_bytes((R/'evidence/native-build-commands.json').read_bytes());print(json.dumps({'files':len(pins),'bytes':sum(x['bytes'] for x in pins.values())}))
