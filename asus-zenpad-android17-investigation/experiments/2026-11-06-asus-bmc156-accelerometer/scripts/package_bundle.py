#!/usr/bin/env python3
from pathlib import Path
import hashlib,json,tarfile,subprocess
S=Path(__file__).resolve().parents[1]
exclude={'artifacts/remote-handoff.tar.gz','artifacts/bmc156-accelerometer-staging.tar.gz','evidence/bundle-receipt.json','evidence/local-verification.txt','bundle-manifest.json'}
files=[]
for root in ['README.md','report','source','scripts','patches','evidence','artifacts/remote']:
 p=S/root
 for f in [p] if p.is_file() else p.rglob('*'):
  if not f.is_file():continue
  rel=str(f.relative_to(S))
  if rel in exclude or '__pycache__' in f.parts or rel.startswith(('evidence/patch-roundtrip/','evidence/oem-patch-roundtrip/')):continue
  files.append(f)
manifest={str(p.relative_to(S)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(files))}
(S/'bundle-manifest.json').write_text(json.dumps(manifest,sort_keys=True,indent=2)+'\n')
p=subprocess.run(['python3',str(S/'scripts/verify_bundle.py')],capture_output=True,text=True);print(p.stdout,p.stderr);assert p.returncode==0
(S/'evidence/local-verification.txt').write_text(p.stdout+p.stderr)
archive=S/'artifacts/bmc156-accelerometer-staging.tar.gz'
with tarfile.open(archive,'w:gz') as t:
 for p in sorted(set(files+[S/'bundle-manifest.json'])):t.add(p,arcname=str(p.relative_to(S)))
receipt=dict(file=str(archive.relative_to(S)),bytes=archive.stat().st_size,sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),files=len(manifest)+1,local_verification=(S/'evidence/local-verification.txt').read_text().strip())
(S/'evidence/bundle-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
