#!/usr/bin/env python3
"""Build a tiny deterministic newc archive, including /dev/console, without root."""
from pathlib import Path
import gzip
import stat
import sys

root = Path(sys.argv[1]) if len(sys.argv) == 2 else Path('/srv/android/asus-virtual-validation')
assert root in [Path('/srv/android/asus-virtual-validation') / name for name in ['', 'ids', 'fd', 'meta']]
archive = bytearray()

def entry(name, mode, contents=b'', major=0, minor=0):
    name_bytes = name.encode() + b'\0'
    fields = [1, mode, 0, 0, 1, 0, len(contents), 0, 0, major, minor, len(name_bytes), 0]
    archive.extend(b'070701' + ''.join(f'{value:08x}' for value in fields).encode())
    archive.extend(name_bytes)
    archive.extend(b'\0' * (-len(archive) % 4))
    archive.extend(contents)
    archive.extend(b'\0' * (-len(archive) % 4))

for name in ['dev', 'proc', 'sys']:
    entry(name, stat.S_IFDIR | 0o755)
entry('dev/console', stat.S_IFCHR | 0o600, major=5, minor=1)
entry('init', stat.S_IFREG | 0o755, (root / 'init').read_bytes())
entry('TRAILER!!!', 0)
(root / 'initramfs.cpio.gz').write_bytes(gzip.compress(archive, mtime=0))
