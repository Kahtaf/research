#!/usr/bin/env python3
"""Upload an immutable revision using the deployed r6 linkerconfig profile."""
import argparse
import io
from pathlib import Path
import re
import subprocess
import tarfile
from graphics_remote import SSH
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--revision',required=True)
args=parser.parse_args()
r=args.revision
assert re.fullmatch(r'r[0-9]+',r)
bundle=io.BytesIO()
with tarfile.open(fileobj=bundle,mode='w') as t:
 for name in ['build_graphics.sh','capture_graphics_revision.py','run_graphics_revision.py',
              'prepare_graphics_blobs.py','deploy_vendor_graphics.py','check_graphics_core_abi.py']:
  t.add(ROOT/'scripts'/name,arcname=f'revisions/{r}/'+name)
 for name in ['linkerconfig.patch','source-manifest.json']:
  t.add(ROOT/'compatibility/graphics-r6'/name,arcname=f'revisions/{r}/'+name)
 t.add(ROOT/f'artifacts/vendor-graphics-inputs-{r}.tar.gz',arcname=f'vendor-graphics-inputs-{r}.tar.gz')
remote='/srv/android/asus-device-product'
subprocess.run(SSH+[f'test ! -e {remote}/revisions/{r} && tar -xf - -C {remote}'],input=bundle.getvalue(),check=True)
script='''from pathlib import Path
import hashlib,json
root=Path('/srv/android/asus-device-product'); tree=Path('/srv/android/lineage24')
expected=json.loads((root/'revisions/r6/source-manifest.json').read_text())
for name,row in expected.items():
 assert hashlib.sha256((tree/'system/linkerconfig'/name).read_bytes()).hexdigest()==row['after_sha256'],name
print('Deployed linkerconfig source verified against r6 manifest')
'''
subprocess.run(SSH+['python3 -'],input=script.encode(),check=True)
subprocess.run(SSH+[f'python3 {remote}/revisions/{r}/prepare_graphics_blobs.py --revision {r} && python3 {remote}/revisions/{r}/deploy_vendor_graphics.py --revision {r}'],check=True)
print(f'{r}: upload, preparation, source verification, deployment all exited 0')
