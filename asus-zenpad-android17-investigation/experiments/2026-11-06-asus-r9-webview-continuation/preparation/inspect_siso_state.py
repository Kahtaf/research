from pathlib import Path
import remote,json
s=r'''
from pathlib import Path
import gzip,json,hashlib
A=Path('/srv/android/lineage24');R=Path('/srv/android/asus-reviewed-build-kit/r9');r={}
for rel in ['out/.siso_fs_state','out/.siso_deps']:
 p=A/rel
 if rel.endswith('fs_state'):
  with gzip.open(p,'rb') as f:b=f.read(128)
  r[rel]=dict(bytes=p.stat().st_size,decoded_first128_hex=b.hex())
 else:r[rel]=dict(bytes=p.stat().st_size)
for phase in ['host_init_verifier','bootimage']:
 p=Path('/srv/android/asus-reviewed-build-kit/r8/attempt/native-evidence')/phase/'siso_metadata.json'
 r[phase]=json.loads(p.read_text()) if p.is_file() else None
with (R/'evidence/siso-state-format.json').open('x') as f:json.dump(r,f,indent=2);f.write('\n')
print(json.dumps(r,indent=2))
'''
r=remote.run(s);Path('2026-11-06-asus-r9-webview-continuation/evidence/siso-state-format.json').write_text(r);print(r[:12000])
