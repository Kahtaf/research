#!/usr/bin/env python3
"""Retain completed framework outputs before the compatibility rebuild changes them."""
import hashlib
import json
from pathlib import Path
import shutil
import tarfile

ROOT = Path('/srv/android/asus-device-product')
PRODUCT = Path('/srv/android/lineage24/out/target/product/p00a')
DEST = ROOT / 'framework-checkpoint'
assert (ROOT / 'logs/framework-build-complete').exists()
log = (ROOT / 'logs/framework-build.log').read_text(errors='replace')
assert 'build completed successfully' in log
assert not DEST.exists(), 'Preserve the previous checkpoint'
DEST.mkdir()
paths = ['system/bin/app_process64', 'system/bin/surfaceflinger',
         'system/framework/framework.jar', 'system/framework/services.jar']
captured = []
missing = []
for relative in paths:
    source = PRODUCT / relative
    if not source.is_file():
        missing.append(relative)
        continue
    destination = DEST / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
    captured.append(relative)
for name in ['framework-build.log', 'framework-build-complete', 'framework-product-vars.txt', 'framework-resume-job.json']:
    source = ROOT / 'logs' / name
    if source.is_file():
        shutil.copyfile(source, DEST / name)
assert 'system/bin/surfaceflinger' in captured and 'system/bin/app_process64' in captured
provenance = dict(scope='Completed SDK 37 ASUS framework module build, before compatibility rebuild',
                  captured=captured, not_installed_by_these_module_targets=missing,
                  android17_boot_validated=False, full_rom_built=False)
(DEST / 'provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')
manifest = [dict(path=str(path.relative_to(DEST)), bytes=path.stat().st_size,
                 sha256=hashlib.sha256(path.read_bytes()).hexdigest())
            for path in sorted(DEST.rglob('*')) if path.is_file()]
(DEST / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
archive = ROOT / 'framework-checkpoint.tar.gz'
with tarfile.open(archive, 'w:gz') as tar:
    tar.add(DEST, arcname=DEST.name)
print(f'Captured {len(captured)} framework artifacts; archive {archive.stat().st_size} bytes')
