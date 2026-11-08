from pathlib import Path
import json,hashlib,base64
R=Path('/srv/android/asus-r9-actual-early-runtime-20261106');files={}
for directory in ['evidence','run-patch-1','run-patch-2','run-runtime-1']:
 for p in (R/directory).iterdir():
  if p.is_file() and p.suffix in ['.json','.log','.txt','.d']:
   assert p.stat().st_size<=4*1024**2
   b=p.read_bytes();files[str(p.relative_to(R))]={'sha256':hashlib.sha256(b).hexdigest(),'base64':base64.b64encode(b).decode()}
assert sum(len(v['base64']) for v in files.values())<8*1024**2
print(json.dumps(files))
