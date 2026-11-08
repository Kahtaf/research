from pathlib import Path
import os,json,hashlib
R=Path('/srv/android/asus-r9-linkerconfig-ownership-fix-20261106');A=Path('/srv/android/lineage24');S=R/'inputs/native-snapshot';os.environ['TMPDIR']=str(R/'tmp');base='prebuilts/gcc/linux-x86/host/x86_64-linux-glibc2.17-4.8';files=[]
for n in ['lib/gcc','lib64/gcc']:
 p=A/base/n
 if p.is_dir():files += [x for x in p.rglob('*') if x.is_file()]
assert sum(p.stat().st_size for p in files)<100*1024**2
pins={}
for p in files:
 rel=str(p.relative_to(A));b=p.read_bytes();dest=S/rel;dest.parent.mkdir(exist_ok=True,parents=True);dest.write_bytes(b);pins[rel]={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
(R/'evidence/host-gcc-runtime-pins.json').write_text(json.dumps(pins,indent=2));(R/'evidence/native-build-failure2.json').write_bytes((R/'evidence/native-build-commands.json').read_bytes());print(json.dumps({'files':len(pins),'bytes':sum(x['bytes'] for x in pins.values()),'top_paths':sorted({str(p.parent.relative_to(A)) for p in files})}))
