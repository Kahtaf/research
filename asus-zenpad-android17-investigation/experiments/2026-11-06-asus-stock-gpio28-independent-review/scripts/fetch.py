from pathlib import Path
import subprocess,sys,tarfile,io,json,hashlib
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R.parent/'2026-11-06-asus-product-input-build-kit/scripts'))
from remote import SSH
script='''from pathlib import Path
import os,resource,signal,hashlib,json,tarfile,sys,shutil
resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(60,60));signal.alarm(120)
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
R=Path('/srv/android/asus-stock-gpio28-review-20261106-r1');O=R/'out';A=R/'artifacts'
assert (R/'evidence/final-verification.json').exists()
for base in [O/'include/generated',O/'arch/arm64/include/generated']:
 for p in base.rglob('*.h'):
  q=A/'kbuild-inputs'/p.relative_to(O);q.parent.mkdir(parents=True,exist_ok=True)
  if not q.exists():shutil.copyfile(p,q)
p=O/'scripts/dtc/dtc';q=A/'host-tools/dtc';q.parent.mkdir(parents=True);shutil.copyfile(p,q)
files={str(p.relative_to(R)):dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for base in [R/'evidence',A] for p in base.rglob('*') if p.is_file()}
assert sum(x['bytes'] for x in files.values())<32*1024**2
(R/'EXPORT-MANIFEST.json').write_text(json.dumps(files,sort_keys=True,indent=2)+'\\n')
with tarfile.open(fileobj=sys.stdout.buffer,mode='w|gz') as t:
 for n in list(files)+['EXPORT-MANIFEST.json']:t.add(R/n,arcname=n,recursive=False)
'''
p=subprocess.run(SSH+['python3 -B -'],input=script.encode(),stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=150)
assert p.returncode==0,p.stderr.decode()
D=R/'remote';D.mkdir()
with tarfile.open(fileobj=io.BytesIO(p.stdout),mode='r:gz') as t:
 manifest=json.load(t.extractfile('EXPORT-MANIFEST.json'))
 for m in t.getmembers():
  assert m.isfile() and not Path(m.name).is_absolute() and '..' not in Path(m.name).parts
  b=t.extractfile(m).read()
  if m.name!='EXPORT-MANIFEST.json':assert hashlib.sha256(b).hexdigest()==manifest[m.name]['sha256'] and len(b)==manifest[m.name]['bytes']
  q=D/m.name;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(b)
(R/'evidence/fetch.json').write_text(json.dumps(dict(files=len(manifest),total_bytes=sum(x['bytes'] for x in manifest.values()),tar_sha256=hashlib.sha256(p.stdout).hexdigest(),all_exported_hashes_verified=True),indent=2)+'\n')
print('Fetched',len(manifest),'verified evidence/artifact files')
