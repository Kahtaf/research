#!/usr/bin/env python3
"""Offline MTK boot packaging; no device access or flashing capability."""
from pathlib import Path
import hashlib
import json
import struct
import zlib

root = Path(__file__).resolve().parents[1]
workspace = root.parent
stock_path = workspace / '2026-11-05-asus-latest-android-feasibility/sources/stock-firmware/boot.img'
kernel_path = workspace / '2026-11-05-asus-android17-kernel-backports/artifacts/linux-bpf-fd/bpf-fd-result/ASUS-P00A-BPF-FD-UNTESTED.Image.gz-dtb'
stock = stock_path.read_bytes()
new_kernel = kernel_path.read_bytes()
assert hashlib.sha256(stock).hexdigest() == 'a175ed39c9e9642756dd28f1d006b39937d17f290da6af69dda6d4b52d6f910d'
assert hashlib.sha256(new_kernel).hexdigest() == '7c7051c147b03ca865b3481d55cd832bc6f2732eef1c0063af9404823b0ceaa4'
assert stock[:8] == b'ANDROID!'
ksize, kaddr, rsize, raddr, second_size, second_addr, tags_addr, page = struct.unpack_from('<8I', stock, 8)
assert page == 2048 and second_size == 0
align = lambda n: (n + page - 1) // page * page
pad = lambda data: data + bytes(align(len(data)) - len(data))
kernel = stock[page:page + ksize]
ramdisk_offset = page + align(ksize)
ramdisk = stock[ramdisk_offset:ramdisk_offset + rsize]
end = ramdisk_offset + align(rsize)
trailer = stock[end:]
for payload, name in [(kernel, b'KERNEL'), (ramdisk, b'ROOTFS')]:
    assert payload[:4] == bytes.fromhex('88168858')
    assert struct.unpack_from('<I', payload, 4)[0] == len(payload) - 512
    assert payload[8:40].split(b'\0')[0] == name

def boot_id(k, r):
    return hashlib.sha1(k + struct.pack('<I', len(k)) + r + struct.pack('<I', len(r)) + struct.pack('<I', 0)).digest() + bytes(12)

assert stock[576:608] == boot_id(kernel, ramdisk)
assert stock[:page] + pad(kernel) + pad(ramdisk) + trailer == stock
decoder = zlib.decompressobj(16 + zlib.MAX_WBITS)
raw = decoder.decompress(new_kernel) + decoder.flush()
assert decoder.eof and raw[56:60] == b'ARMd'
assert hashlib.sha256(decoder.unused_data).hexdigest() == '577a1ca5fbfe646ca02a50c190ac60efab0edd73c77c904a33865859e2d87bfc'
wrapper = bytearray(kernel[:512])
struct.pack_into('<I', wrapper, 4, len(new_kernel))
wrapped_kernel = bytes(wrapper) + new_kernel
header = bytearray(stock[:page])
struct.pack_into('<I', header, 8, len(wrapped_kernel))
header[576:608] = boot_id(wrapped_kernel, ramdisk)
# The ASUS signature belongs to the original payload and cannot authenticate
# this changed kernel. Do not copy it onto the experimental output.
image = bytes(header) + pad(wrapped_kernel) + pad(ramdisk)
layout = json.loads((workspace / '2026-11-05-asus-latest-android-feasibility/evidence/live-partition-layout.json').read_text())
partition_size = next(p['size_bytes'] for p in layout if p['name'] == 'boot')
assert len(image) <= partition_size
changed = [i for i in range(page) if header[i] != stock[i]]
assert all(8 <= i < 12 or 576 <= i < 608 for i in changed)
new_offset = page + align(len(wrapped_kernel))
assert image[new_offset:new_offset + rsize] == ramdisk
assert image[576:608] == boot_id(image[page:page + len(wrapped_kernel)], ramdisk)
output = root / 'artifacts/EXPERIMENTAL-KERNEL-4.9-STOCK-RAMDISK.img'
with output.open('xb') as stream:
    stream.write(image)
report = {'stock_roundtrip_exact': True, 'stock_trailer_bytes': len(trailer),
          'output': output.name, 'bytes': len(image), 'partition_bytes': partition_size,
          'sha256': hashlib.sha256(image).hexdigest(), 'kernel_load_address': hex(kaddr),
          'ramdisk_load_address': hex(raddr), 'second_load_address': hex(second_addr),
          'tags_address': hex(tags_addr), 'page_bytes': page,
          'stock_ramdisk_unchanged': True, 'new_mtk_kernel_bytes': len(wrapped_kernel),
          'boot_header_id_valid': True, 'asus_signature_valid': False,
          'android17_userspace_included': False, 'hardware_boot_validated': False,
          'purpose': 'Kernel packaging step toward Android 17; not ready for hardware boot or flashing'}
(root / 'evidence/kernel-packaging.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
