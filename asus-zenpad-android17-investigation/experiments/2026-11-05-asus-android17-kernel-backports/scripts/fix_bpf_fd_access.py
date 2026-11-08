#!/usr/bin/env python3
"""Preserve the failed virtual evidence and correct the older FD access flags."""
from pathlib import Path
import json
import shutil
import subprocess

root = Path('/srv/android/asus-virtual-validation')
source = root / 'kernel-fd'
test = root / 'fd'
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=source, text=True).strip() == '83e07819d5fece96a2c62bf44f9da759067bbe6b'
result = json.loads((test / 'logs/qemu-result.json').read_text())
assert result['fd_checks']['lookup_persistence'] == 0
failed = test / 'first-runtime-failure'
failed.mkdir()
for relative in ['logs/qemu-boot.log', 'logs/qemu-result.json', 'init', 'initramfs.cpio.gz',
                 'bpf_fd_checks.h', 'bpf_smoke_init.c', 'bpf-fd.patch']:
    path = test / relative
    shutil.copy2(path, failed / path.name)
p = source / 'kernel/bpf/syscall.c'
text = p.read_text()
old = 'fd = bpf_map_new_fd(map, 0);'
assert text.count(old) == 1
p.write_text(text.replace(old, 'fd = bpf_map_new_fd(map, O_RDWR);'))
subprocess.run(['git', 'add', 'kernel/bpf/syscall.c'], cwd=source, check=True)
subprocess.run(['git', 'commit', '-m', 'bpf: preserve read/write access when opening a map by ID'], cwd=source, check=True)
metadata = json.loads((test / 'source-provenance.json').read_text())
metadata['revision'] = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=source, text=True).strip()
metadata['initial_failed_revision'] = '83e07819d5fece96a2c62bf44f9da759067bbe6b'
metadata['correction'] = 'The legacy constructor takes O_* file access flags; 0 means O_RDONLY, so use O_RDWR.'
(test / 'source-provenance.json').write_text(json.dumps(metadata, indent=2) + '\n')
(test / 'bpf-fd.patch').write_bytes(subprocess.check_output(['git', 'format-patch', metadata['baseline'] + '..HEAD', '--stdout'], cwd=source))
for name in ['qemu-boot.log', 'qemu-result.json']:
    (test / 'logs' / name).unlink()
print(json.dumps(metadata, indent=2))
