"""Collect compact artifacts. Full padded p10/payload/test initramfs stay on VM."""
from remote import R,REMOTE,call
from pathlib import Path
import io,tarfile,json,hashlib
code='''from pathlib import Path
import tarfile,io,sys
r=Path(REMOTE)
names=['ARTIFACTS.json','SOURCE_PINS.json','tests/probe_binding.h']
for directory in ['source','evidence']:
 names += [str(p.relative_to(r)) for p in (r/directory).rglob('*') if p.is_file() and '__pycache__' not in str(p)]
names += ['artifacts/'+n for n in ['base-header','base-kernel','base-wrapper','base-policy','original-stock.manifest','file_contexts','file_contexts.bin','restore-sepolicy','os-rescue','p10-restore','p10-restore-reproduction','legacy-reproduction','rescue-proxy','core.cpio.gz','core-entries.json','core-input-metadata.json','candidate/UNAPPROVED-STOCK-ONLY.img','candidate/helper.cpio','candidate/session-contract.UNAPPROVED.json']]
with tarfile.open(fileobj=sys.stdout.buffer,mode='w|') as t:
 for name in names:t.add(r/name,arcname=name,recursive=False)
'''.replace('REMOTE',repr(REMOTE))
p=call(code,timeout=120);assert p.returncode==0,p.stderr
with tarfile.open(fileobj=io.BytesIO(p.stdout)) as t:
 for m in t.getmembers():
  assert m.isfile() and not m.name.startswith('/') and '..' not in Path(m.name).parts
  target=R/m.name
  if target.exists() and target.read_bytes()!=t.extractfile(m).read():
   # Generated source pins are expected to change; preserve every prior byte.
   previous=R/'evidence/local-before-collection'/m.name;previous.parent.mkdir(parents=True,exist_ok=True);previous.write_bytes(target.read_bytes())
 t.extractall(R,filter='data')
for rel,entry in json.loads((R/'ARTIFACTS.json').read_text()).items():
 p=R/rel
 if p.exists():assert hashlib.sha256(p.read_bytes()).hexdigest()==entry['sha256'],rel
print('COMPACT_DELIVERY_COLLECTED_AND_HASH_VERIFIED')
