#!/usr/bin/env python3
"""Archive the first successful virtual test before any further feature work."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import tarfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--candidate', choices=['baseline', 'ids', 'fd'], default='baseline')
args = parser.parse_args()
base = Path('/srv/android/asus-virtual-validation')
root = base / args.candidate if args.candidate != 'baseline' else base
result = json.loads((root / 'logs/qemu-result.json').read_text())
assert result['basic_bpf_passed'] and result['smoke_completed']
assert result['qemu_returncode'] == 0 and not result['timed_out']
if args.candidate != 'baseline':
    assert result['ids']['all_checks_passed']
if args.candidate == 'fd':
    assert result['fd_checks']['all_checks_passed']
out = root / (args.candidate + '-result')
out.mkdir()
files = {'VIRTUAL-ONLY.Image': root / 'build/arch/arm64/boot/Image',
         'kernel.config': root / 'build/.config'}
for name in ['init', 'initramfs.cpio.gz', 'source-provenance.json', 'bpf_smoke_init.c', 'make_initramfs.py']:
    files[name] = root / name
for name in ['gic-platform-guard.patch', 'build_virtual.sh', 'run_virtual.py', 'prepare_virtual.py']:
    files[name] = base / name
logs = ['qemu-boot.log', 'qemu-result.json', 'build.log', 'config.log', 'build-complete', 'artifact-hashes.txt']
if args.candidate == 'baseline':
    logs += ['first-build-failure.log', 'second-build-failure.log', 'first-build.config']
elif args.candidate == 'ids':
    files['bpf-ids.patch'] = root / 'bpf-ids.patch'
    files['prepare_bpf_ids.py'] = base / 'prepare_bpf_ids.py'
else:
    for name in ['bpf-fd.patch', 'bpf_fd_checks.h']:
        files[name] = root / name
    for name in ['prepare_bpf_fd.py', 'fix_bpf_fd_access.py']:
        files[name] = base / name
for name in logs:
    files[name] = root / 'logs' / name
for name, source in files.items():
    shutil.copy2(source, out / name)
if args.candidate == 'fd':
    shutil.copytree(root / 'first-runtime-failure', out / 'first-runtime-failure')
(out / 'README.txt').write_text('QEMU generic ARM64 kernel/BPF test only. Not Android 17 userspace. Not an ASUS hardware image. NEVER FLASH.\n')
manifest = [{'path': str(path.relative_to(out)), 'bytes': path.stat().st_size,
             'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
            for path in sorted(out.rglob('*')) if path.is_file()]
(out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
archive = root / ('virtual-' + args.candidate + '-checkpoint.tar.gz')
assert not archive.exists()
with tarfile.open(archive, 'w:gz') as bundle:
    bundle.add(out, arcname=args.candidate + '-result')
print(json.dumps({'files': len(manifest), 'bytes': archive.stat().st_size,
                  'sha256': hashlib.sha256(archive.read_bytes()).hexdigest()}, indent=2))
