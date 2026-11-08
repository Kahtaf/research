#!/usr/bin/env python3
"""Deterministic metadata-only repair. No device/network/build-machine operations."""
import hashlib
import importlib.util
import json
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT.parent
BASE = WORK / '2026-11-06-asus-android17-build-continuation'
OLD = BASE / 'artifacts/probe-r2/UNTESTED-combined-linux49-ram-probe.img'
COMPILED = BASE / 'artifacts/Image.gz-dtb-combined-r1'
OLD_SHA = '48bb6efa1620cb380037e53b53cfa560e38cd23b95211c8634616ce94fd6ce48'
COMPILED_SHA = 'd4094bcff6c763af7f1c01ccd3d612a988f96de13f78b492b808cc76c0ac929f'


def sha(value):
    return hashlib.sha256(value).hexdigest()


def load(name, filename, expected):
    path = BASE / 'probe' / filename
    assert sha(path.read_bytes()) == expected, 'Pinned metadata helper changed'
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def build():
    boot = load('pinned_boot', 'bootformat.py', '3207680c9c4fdee2c2dc3704cb3564e5c3736c0eb3cae63edb17f6d5fa958017')
    dt = load('pinned_dt', 'fdt.py', '1bd710a08eae5677689a52042a621f39dcd57e49197749cf2833eead1fc0dcae')
    old, compiled = OLD.read_bytes(), COMPILED.read_bytes()
    assert sha(old) == OLD_SHA and sha(compiled) == COMPILED_SHA
    header, old_kernel, ramdisk, tail = boot.parse_image(old)
    assert not tail and len(old) == 8880128
    raw, original_dt = boot.ungzip(compiled)
    stream = compiled[:-len(original_dt)]
    assert sha(stream) == 'acd66b0e487c9b3cf6170b471847e5b6b83478ca50a00ce6c7cbcae8401951e5'
    assert old_kernel[512:512 + len(stream)] == stream
    start, length = 0x44000000, len(ramdisk) - 512
    assert length == 1177520 and struct.unpack_from('<I', header, 20)[0] == start
    corrected_dt = dt.exact_initrd(original_dt, start, length)
    _, before, _ = dt.parse(original_dt)
    _, after, _ = dt.parse(corrected_dt)
    changes = {(node, prop) for node in before.keys() | after.keys()
               for prop in before.get(node, {}).keys() | after.get(node, {}).keys()
               if before.get(node, {}).get(prop) != after.get(node, {}).get(prop)}
    assert changes == {('/chosen', 'bootargs'), ('/chosen', 'linux,initrd-start'), ('/chosen', 'linux,initrd-end')}
    old_cmd = header[64:576].split(b'\0')[0]
    old_token = b'initrd=0x44000200,0x11f7b0'
    token = b'initrd=0x44000000,0x11f7b0'
    assert [t for t in old_cmd.split() if t.startswith(b'initrd=')] == [old_token]
    cmd = old_cmd.replace(old_token, token)
    assert len(cmd) == 95 and len(cmd) <= 99  # Exact LK snprintf(header,100).
    new_header = bytearray(header)
    new_header[64:576] = cmd + bytes(512 - len(cmd))
    kernel = boot.wrap(old_kernel, stream + corrected_dt)
    image = boot.make_image(new_header, kernel, ramdisk)
    h, k, r, tail = boot.parse_image(image)
    assert not tail and r == ramdisk and k[512:512 + len(stream)] == stream
    assert h[:64] == header[:64] and h[608:] == header[608:]
    assert boot.ungzip(k[512:])[0] == raw
    assert int.from_bytes(after['/chosen']['linux,initrd-start'], 'big') == start
    assert int.from_bytes(after['/chosen']['linux,initrd-end'], 'big') == start + length
    assert [t for t in after['/chosen']['bootargs'].rstrip(b'\0').split() if t.startswith(b'initrd=')] == [token]
    assert ramdisk[512:514] == b'\x1f\x8b'
    out = ROOT / 'artifacts/probe-r3'
    out.mkdir(parents=True, exist_ok=False)
    name = 'UNTESTED-combined-linux49-ram-probe-r3.img'
    (out / name).write_bytes(image)
    (out / 'packaged.dtb').write_bytes(corrected_dt)
    result = {'status': 'HOST_METADATA_REPAIRED_PHYSICAL_UNTESTED', 'candidate': name,
              'image_bytes': len(image), 'image_sha256': sha(image),
              'padded_partition_sha256': sha(image + bytes(boot.PARTITION_SIZE - len(image))),
              'old_image_sha256': OLD_SHA, 'compiled_input_sha256': COMPILED_SHA,
              'header_page_sha256': sha(h), 'packaged_dtb_sha256': sha(corrected_dt),
              'compressed_image_sha256': sha(stream), 'wrapped_ramdisk_sha256': sha(ramdisk),
              'ramdisk_gzip_sha256': sha(ramdisk[512:]), 'ramdisk_bytes': length,
              'ramdisk_start': hex(start), 'ramdisk_end': hex(start + length),
              'header_cmdline': cmd.decode(), 'lk_header_limit_bytes': 99,
              'dt_changed_properties': sorted(changes), 'compressed_image_unchanged': True,
              'entire_wrapped_ramdisk_unchanged': True, 'device_operations': 0,
              'physical_boot_proven': False, 'transport_profile_ready': False,
              'builder_sha256': sha(Path(__file__).read_bytes())}
    (out / 'manifest.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    build()
