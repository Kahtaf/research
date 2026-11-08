#!/usr/bin/env python3
"""Inspect the two matching recovery backups without executing/extracting files."""
from pathlib import Path
import hashlib
import json
import struct
import zlib

root = Path(__file__).resolve().parents[1]
first = root / 'artifacts/device-backup/initial/recovery.bin'
second = root / 'artifacts/device-backup/verify/recovery.bin'
image = first.read_bytes()
assert image == second.read_bytes(), 'Recovery backups differ'
assert hashlib.sha256(image).hexdigest() == '902b2f06a01cca574b4aa374e67c4e7f8f0ed53f6e6a55017b6d96351f0f1f20'
assert image[:8] == b'ANDROID!'
kernel_size, _, ramdisk_size, _, _, _, _, page = struct.unpack_from('<8I', image, 8)
assert page == 2048
align = lambda value, multiple: (value + multiple - 1) // multiple * multiple
start = page + align(kernel_size, page)
ramdisk = image[start:start + ramdisk_size]
assert len(ramdisk) == ramdisk_size
assert ramdisk[:4] == bytes.fromhex('88168858')
wrapper_name = ramdisk[8:40].split(b'\0')[0].decode('ascii')
assert struct.unpack_from('<I', ramdisk, 4)[0] == ramdisk_size - 512
decoder = zlib.decompressobj(16 + zlib.MAX_WBITS)
cpio = decoder.decompress(ramdisk[512:], 64 * 1024 * 1024)
assert decoder.eof and not decoder.unconsumed_tail, 'Invalid or oversized ramdisk'
entries, text_files = [], {}
position = 0
while True:
    header = cpio[position:position + 110]
    assert header[:6] in [b'070701', b'070702']
    fields = [int(header[6 + 8*i:14 + 8*i], 16) for i in range(13)]
    size, name_size = fields[6], fields[11]
    assert 0 < name_size < 4096
    name = cpio[position + 110:position + 110 + name_size - 1].decode()
    position = align(position + 110 + name_size, 4)
    contents = cpio[position:position + size]
    assert len(contents) == size
    position = align(position + size, 4)
    if name == 'TRAILER!!!':
        break
    entries.append({'name': name, 'mode': oct(fields[1]), 'bytes': size,
                    'sha256': hashlib.sha256(contents).hexdigest()})
    basename = Path(name).name
    if (basename == 'default.prop' or (basename.startswith('init') and basename.endswith('.rc'))
            or 'fstab' in basename) and size < 100000:
        text_files[name] = contents.decode('utf-8')
report = {'input_sha256': hashlib.sha256(image).hexdigest(),
          'kernel_bytes': kernel_size, 'ramdisk_bytes': ramdisk_size,
          'wrapper_name': wrapper_name, 'cpio_bytes': len(cpio),
          'entries': entries, 'configuration': text_files,
          'device_rebooted': False, 'recovery_runtime_validated': False}
output = root / 'evidence/stock-recovery-ramdisk-audit.json'
output.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'wrapper_name': wrapper_name, 'entries': len(entries),
                  'configuration_files': sorted(text_files), 'report': str(output)}, indent=2))
