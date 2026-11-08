#!/usr/bin/env python3
"""Capture successful SDK 37 networking module outputs with source provenance."""
from pathlib import Path
import hashlib
import json
import shutil
import struct
import subprocess
import tarfile

root = Path('/srv/android/asus-device-product')
platform = Path('/srv/android/lineage24')
assert (root / 'logs/network-build-complete').exists()
out = root / 'network-result'
out.mkdir()
products = {
    'netd': ('out/target/product/p00a/system/bin/netd', 183),
    'netbpfload': ('out/soong/.intermediates/packages/modules/Connectivity/bpf/loader/netbpfload/android_arm64_armv8-a_apex31/netbpfload', 183),
    'netd.o': ('out/soong/.intermediates/packages/modules/Connectivity/bpf/progs/netd.o/android_common/obj/packages/modules/Connectivity/bpf/progs/netd.o', 247),
}
elf = {}
for name, (relative, machine) in products.items():
    source = platform / relative
    data = source.read_bytes()
    assert data[:6] == b'\x7fELF\x02\x01'
    actual = struct.unpack_from('<H', data, 18)[0]
    assert actual == machine, (name, actual)
    shutil.copy2(source, out / name)
    elf[name] = {'machine': actual, 'class': 64, 'source': relative}
for relative in ['network-build.log', 'network-build-complete', 'network-product-vars.txt']:
    shutil.copy2(root / 'logs' / relative, out / relative)
for relative in ['BoardConfig.mk', 'device.mk', 'lineage_p00a.mk', 'AndroidProducts.mk']:
    destination = out / 'device/asus/p00a' / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(platform / 'device/asus/p00a' / relative, destination)
pins = {name: subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=platform / name, text=True).strip()
        for name in ['packages/modules/Connectivity', 'system/netd', 'bionic', 'kernel/asus/p00a']}
metadata = {'sdk': 37, 'android': 17, 'source_revisions': pins, 'elf': elf,
            'build': 'netd netbpfload netd.o', 'runtime_validated': False,
            'flashable_rom': False, 'kernel_requirements_satisfied': False}
(out / 'provenance.json').write_text(json.dumps(metadata, indent=2) + '\n')
manifest = []
for path in sorted(out.rglob('*')):
    if path.is_file():
        manifest.append({'path': str(path.relative_to(out)), 'bytes': path.stat().st_size,
                         'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
(out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
archive = root / 'network-checkpoint.tar.gz'
assert not archive.exists()
with tarfile.open(archive, 'w:gz') as bundle:
    bundle.add(out, arcname='network-result')
print(json.dumps({'files': len(manifest), 'archive': str(archive), 'bytes': archive.stat().st_size,
                  'sha256': hashlib.sha256(archive.read_bytes()).hexdigest()}, indent=2))
