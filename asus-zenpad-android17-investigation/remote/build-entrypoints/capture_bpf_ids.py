#!/usr/bin/env python3
"""Capture a compiled ASUS BPF candidate and its virtual-test equivalence."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import subprocess
import tarfile

root = Path('/srv/android/asus-android17')
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--candidate', choices=['ids', 'fd'], default='ids')
args = parser.parse_args()
feature = args.candidate
source = root / ('kernel-bpf-' + feature)
virtual = Path('/srv/android/asus-virtual-validation')
assert (root / ('logs/bpf-' + feature + '-hardware-build-complete')).exists()
runtime = json.loads((virtual / feature / 'logs/qemu-result.json').read_text())
assert runtime['ids']['all_checks_passed'] and runtime['qemu_returncode'] == 0
if feature == 'fd':
    assert runtime['fd_checks']['all_checks_passed']
core_hashes = {}
for relative in ['include/linux/bpf.h', 'include/uapi/linux/bpf.h', 'kernel/bpf/syscall.c']:
    first = (source / relative).read_bytes()
    assert first == (virtual / ('kernel-' + feature) / relative).read_bytes(), relative
    core_hashes[relative] = hashlib.sha256(first).hexdigest()
out = root / ('bpf-' + feature + '-result')
out.mkdir()
files = {
    'ASUS-P00A-BPF-' + feature.upper() + '-UNTESTED.Image.gz-dtb': root / ('build-bpf-' + feature) / 'arch/arm64/boot/Image.gz-dtb',
    'asus-p00a.dtb': root / ('build-bpf-' + feature) / 'arch/arm64/boot/dts/mediatek/asus-p00a.dtb',
    'kernel.config': root / ('build-bpf-' + feature) / '.config',
    'bpf-' + feature + '.patch': virtual / feature / ('bpf-' + feature + '.patch'),
    'qemu-result.json': virtual / feature / 'logs/qemu-result.json',
}
names = ['bpf-' + feature + '-hardware-' + suffix for suffix in
         ['build.log', 'config.log', 'build-complete', 'artifact-hashes.txt', 'source.txt']]
names.append('bpf-' + feature + '-capability-audit.json')
for name in names:
    files[name] = root / 'logs' / name
for name, path in files.items():
    shutil.copy2(path, out / name)
metadata = {'source_revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=source, text=True).strip(),
            'virtual_revision': runtime['source']['revision'], 'identical_tested_core_files': core_hashes,
            'virtual_gic_change_imported': False, 'asus_hardware_runtime_validated': False,
            'charging_enabled': False, 'complete_boot_image': False, 'flashable_rom': False}
(out / 'provenance.json').write_text(json.dumps(metadata, indent=2) + '\n')
manifest = [{'path': p.name, 'bytes': p.stat().st_size,
             'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
            for p in sorted(out.iterdir()) if p.is_file()]
(out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
archive = root / ('bpf-' + feature + '-checkpoint.tar.gz')
assert not archive.exists()
with tarfile.open(archive, 'w:gz') as bundle:
    bundle.add(out, arcname='bpf-' + feature + '-result')
print(json.dumps({'files': len(manifest), 'bytes': archive.stat().st_size,
                  'sha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
                  'image': next(row for row in manifest if row['path'].endswith('Image.gz-dtb'))}, indent=2))
