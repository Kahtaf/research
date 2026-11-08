from pathlib import Path
import sys,subprocess,tarfile,io,json,hashlib,shutil
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'2026-11-06-asus-product-input-build-kit/scripts'))
from remote import SSH
L=Path(__file__).resolve().parents[1]
assert L.name=='2026-11-06-asus-bmc156-full-kernel' and not L.is_symlink() and shutil.disk_usage(L).free>128*1024**2
script='''from pathlib import Path
import sys,tarfile,json,hashlib,os
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
R=Path('/srv/android/asus-bmc156-full-kernel-r1/export-compact');manifest=json.loads((R/'MANIFEST.json').read_text())
assert manifest['total_bytes']<12*1024**2
for rel,v in manifest['files'].items():
 p=R/rel;assert p.is_file() and not p.is_symlink() and p.resolve().is_relative_to(R)
 assert hashlib.sha256(p.read_bytes()).hexdigest()==v['sha256']
with tarfile.open(fileobj=sys.stdout.buffer,mode='w|') as t:
 for rel in sorted(list(manifest['files'])+['MANIFEST.json']):t.add(R/rel,arcname=rel,recursive=False)
'''
p=subprocess.run(SSH+['python3 -B -'],input=script.encode(),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
assert p.returncode==0,p.stderr.decode()
with tarfile.open(fileobj=io.BytesIO(p.stdout)) as t:
 manifest=json.load(t.extractfile('MANIFEST.json'))
 for m in t.getmembers():
  assert m.isfile() and not Path(m.name).is_absolute() and '..' not in Path(m.name).parts
  b=t.extractfile(m).read()
  if m.name!='MANIFEST.json':
   v=manifest['files'][m.name];assert len(b)==v['bytes'] and hashlib.sha256(b).hexdigest()==v['sha256']
  dest=L/m.name;assert dest.resolve().is_relative_to(L)
  if dest.exists():assert dest.read_bytes()==b,('Existing local file differs',m.name)
  else:dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(b)
receipt=dict(transport='authorized SSH helper identity by path only; in-memory tar stream',files=len(manifest['files']),bytes=manifest['total_bytes'],transport_archive_sha256=hashlib.sha256(p.stdout).hexdigest(),all_payload_hashes_passed=True)
(L/'evidence/local-fetch.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
