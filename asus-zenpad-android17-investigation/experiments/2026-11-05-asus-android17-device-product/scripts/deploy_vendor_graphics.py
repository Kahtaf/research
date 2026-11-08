#!/usr/bin/env python3
"""Deploy a verified revision, preserving the previous source and stale outputs."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path('/srv/android/asus-device-product')
TREE = Path('/srv/android/lineage24')
parser = argparse.ArgumentParser()
parser.add_argument('--revision', required=True)
args = parser.parse_args()
assert re.fullmatch(r'r[0-9]+', args.revision)
SOURCE = ROOT / ('staged-vendor-' + args.revision) / 'vendor/asus/p00a'
DEST = TREE / 'vendor/asus/p00a'
manifest = json.loads((SOURCE / 'ready-manifest.json').read_text())
for row in manifest:
    assert hashlib.sha256((SOURCE / row['path']).read_bytes()).hexdigest() == row['sha256']
active = subprocess.run(['pgrep', '-af', r'out/soong_ui --build-mode|prebuilts/siso/linux-x86/siso|/ninja |/soong_build '], capture_output=True, text=True)
assert not active.stdout.strip(), 'A platform build is active: ' + active.stdout
if DEST.exists() and (DEST / 'ready-manifest.json').read_bytes() == (SOURCE / 'ready-manifest.json').read_bytes():
    for row in manifest:
        assert hashlib.sha256((DEST / row['path']).read_bytes()).hexdigest() == row['sha256']
    print('Exact revision already deployed')
else:
    backup = ROOT / ('before-graphics-' + args.revision)
    assert not backup.exists()
    backup.mkdir()
    if DEST.exists():
        old = json.loads((DEST / 'input-manifest.json').read_text())
        shutil.move(str(DEST), backup / 'vendor-source')
        # Preserve stale installed vendor blobs so a later image cannot select
        # them ahead of this revision's system libraries. No clean rebuild.
        for item in old:
            rel = Path(item['path']).relative_to('proprietary')
            for prefix in ['system/vendor', 'symbols/system/vendor']:
                installed = TREE / 'out/target/product/p00a' / prefix / rel
                if installed.exists() or installed.is_symlink():
                    saved = backup / 'outputs' / prefix / rel
                    saved.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(installed), saved)
    shutil.copytree(SOURCE, DEST)
    for row in manifest:
        assert hashlib.sha256((DEST / row['path']).read_bytes()).hexdigest() == row['sha256']
    print(f'Deployed {args.revision}; previous inputs/outputs preserved at {backup}')
(ROOT / f'logs/graphics-deploy-{args.revision}.json').write_text(json.dumps(dict(
    revision=args.revision, verified_files=len(manifest), exit_status=0), indent=2)+'\n')
