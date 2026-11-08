import remote,json
from pathlib import Path
s=r'''
from pathlib import Path
import json
A=Path('/srv/android/lineage24/out');R=Path('/srv/android/asus-reviewed-build-kit/r9');rows=[]
for p in A.iterdir():
 if any(s in p.name.lower() for s in ['siso','ninja','cache','dep']):
  r=dict(name=p.name,bytes=p.stat().st_size,is_dir=p.is_dir())
  if p.is_file():
   with p.open('rb') as f:r['first32_hex']=f.read(32).hex()
  rows.append(r)
dictout=dict(scope='Top-level names, sizes and magic only; no cache mutation or build engine invocation.',stores=rows)
with (R/'evidence/cache-store-inventory.json').open('x') as f:json.dump(dictout,f,indent=2);f.write('\n')
print(json.dumps(dictout,indent=2))
'''
r=remote.run(s);Path('2026-11-06-asus-r9-webview-continuation/evidence/cache-store-inventory.json').write_text(r);print(r)
