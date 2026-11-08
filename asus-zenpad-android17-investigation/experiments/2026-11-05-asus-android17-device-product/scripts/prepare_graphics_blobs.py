#!/usr/bin/env python3
"""Prepare a fresh numbered graphics revision; change only recorded DT_NEEDED."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tarfile

ROOT = Path('/srv/android/asus-device-product')
parser = argparse.ArgumentParser()
parser.add_argument('--revision', required=True)
args = parser.parse_args()
assert re.fullmatch(r'r[0-9]+', args.revision)
OUT = ROOT / ('staged-vendor-' + args.revision)
assert not OUT.exists(), 'Preserve prior revisions; never patch twice'
with tarfile.open(ROOT / ('vendor-graphics-inputs-' + args.revision + '.tar.gz')) as archive:
    archive.extractall(OUT, filter='data')
source = OUT / 'vendor/asus/p00a'
manifest = json.loads((source / 'input-manifest.json').read_text())
rows = []
for item in manifest:
    output = source / item['path']
    assert hashlib.sha256(output.read_bytes()).hexdigest() == item['original_sha256']
    before = subprocess.check_output(['patchelf', '--print-needed', str(output)], text=True).splitlines()
    assert before == item['original_needed']
    for name in item['additional_dependencies']:
        assert name not in before
        subprocess.run(['patchelf', '--page-size', '4096', '--add-needed', name, str(output)], check=True)
    after = subprocess.check_output(['patchelf', '--print-needed', str(output)], text=True).splitlines()
    assert set(after) == set(before) | set(item['additional_dependencies'])
    rows.append(dict(item, sha256=hashlib.sha256(output.read_bytes()).hexdigest(), needed=after))
(source / 'adaptation-manifest.json').write_text(json.dumps(dict(
    revision=args.revision, patchelf=subprocess.check_output(['patchelf','--version'], text=True).strip(),
    files=rows, scope='DT_NEEDED only; stock archive preserved; core ABI; no hardware test'), indent=2)+'\n')
ready = [dict(path=str(p.relative_to(source)), sha256=hashlib.sha256(p.read_bytes()).hexdigest())
         for p in sorted(source.rglob('*')) if p.is_file()]
(source / 'ready-manifest.json').write_text(json.dumps(ready, indent=2)+'\n')
print(f'Prepared {args.revision}: {len(rows)} ELF files; {len(ready)} hash-recorded inputs')
