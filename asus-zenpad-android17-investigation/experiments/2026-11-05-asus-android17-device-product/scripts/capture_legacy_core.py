#!/usr/bin/env python3
"""Capture completed Android 17 boot userspace and the actual ASUS services."""
from pathlib import Path
import hashlib
import json
import shutil
import struct
import subprocess
import tarfile

ROOT = Path('/srv/android/asus-device-product')
PRODUCT = Path('/srv/android/lineage24/out/target/product/p00a')
DEST = ROOT / 'legacy-core-checkpoint'
assert (ROOT / 'logs/legacy-core-build-complete').exists()
assert not DEST.exists(), 'Keep the previous checkpoint'
DEST.mkdir()
paths = ['ramdisk/init', 'system/bin/init', 'system/bin/bootstrap/linker64',
         'system/bin/toybox', 'system/bin/sh', 'system/bin/linkerconfig',
         'system/bin/netd', 'system/framework/services.jar',
         'system/vendor/bin/hw/android.hardware.lights-service.asus-p00a',
         'system/vendor/lib/libp00a_legacy_memory.so',
         'system/vendor/lib64/libp00a_legacy_memory.so',
         'system/lib64/bootstrap/libc.so', 'system/lib/bootstrap/libc.so']
for relative in paths:
    source = PRODUCT / relative
    assert source.is_file(), str(source)
    output = DEST / relative
    output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, output)
first = (DEST / 'ramdisk/init').read_bytes()
assert first[:5] == b'\x7fELF\x02' and struct.unpack_from('<H', first, 18)[0] == 183
phoff = struct.unpack_from('<Q', first, 32)[0]
entsize, count = struct.unpack_from('<HH', first, 54)
assert all(struct.unpack_from('<I', first, phoff + n * entsize)[0] != 3 for n in range(count))
for name in ['legacy-core-build-complete', 'legacy-userspace-build.log']:
    shutil.copyfile(ROOT / 'logs' / name, DEST / name)
shutil.copyfile(ROOT / 'compatibility/applied.json', DEST / 'applied-platform-patches.json')
provenance = dict(sdk=37, android=17, static_arm64_first_stage_init=True,
                  scope='Completed core module build; no full ROM or ASUS hardware boot',
                  source_heads=json.loads((ROOT / 'compatibility/applied.json').read_text())['projects'])
(DEST / 'provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')
manifest = [dict(path=str(path.relative_to(DEST)), bytes=path.stat().st_size,
                 sha256=hashlib.sha256(path.read_bytes()).hexdigest())
            for path in sorted(DEST.rglob('*')) if path.is_file()]
(DEST / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
archive = ROOT / 'legacy-core-checkpoint.tar.gz'
with tarfile.open(archive, 'w:gz') as tar:
    tar.add(DEST, arcname=DEST.name)
print(json.dumps(dict(files=len(manifest), archive_bytes=archive.stat().st_size,
                      archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
                      first_stage_init_bytes=len(first)), indent=2))
