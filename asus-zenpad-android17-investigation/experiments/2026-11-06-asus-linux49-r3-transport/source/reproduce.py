#!/usr/bin/env python3
"""Replay the pinned metadata builder into this spike; never mutate source images."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT.parent
FIX = WORK / '2026-11-06-asus-linux49-probe-initrd-fix'
BUILDER_SHA = '4e54aaf22d75ebc6a2a8fe956e0bb60534c342d9ca94b2a216e78c4b4287207e'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def reproduce(out):
    assert ROOT in out.resolve().parents and not out.exists(), 'Use a new output directory inside this spike'
    path = ROOT / 'evidence/reference/build.py'
    assert sha(path.read_bytes()) == BUILDER_SHA
    assert sha((FIX / 'source/build.py').read_bytes()) == BUILDER_SHA
    spec = importlib.util.spec_from_file_location('pinned_metadata_builder', path)
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    builder.ROOT = out
    builder.WORK = WORK
    builder.BASE = WORK / '2026-11-06-asus-android17-build-continuation'
    builder.OLD = builder.BASE / 'artifacts/probe-r2/UNTESTED-combined-linux49-ram-probe.img'
    builder.COMPILED = builder.BASE / 'artifacts/Image.gz-dtb-combined-r1'
    builder.build()
    artifact = out / 'artifacts/probe-r3'
    manifest = json.loads((FIX / 'artifacts/probe-r3/manifest.json').read_text())
    data = (artifact / manifest['candidate']).read_bytes()
    original = (FIX / 'artifacts/probe-r3' / manifest['candidate']).read_bytes()
    assert data == original and sha(data) == manifest['image_sha256']
    assert (artifact / 'manifest.json').read_bytes() == (FIX / 'artifacts/probe-r3/manifest.json').read_bytes()
    boot = builder.load('cpio_verify', 'bootformat.py', '3207680c9c4fdee2c2dc3704cb3564e5c3736c0eb3cae63edb17f6d5fa958017')
    dt = builder.load('dt_verify', 'fdt.py', '1bd710a08eae5677689a52042a621f39dcd57e49197749cf2833eead1fc0dcae')
    h, k, r, tail = boot.parse_image(data)
    raw, trailing = boot.ungzip(r[512:])
    assert not trailing and not tail
    entries = {name: {'mode': oct(mode), 'uid': uid, 'gid': gid, 'bytes': len(value), 'sha256': sha(value)}
               for name, (mode, uid, gid, value) in boot.parse_cpio(raw).items()}
    profile = json.loads((ROOT / 'profile.json').read_text())
    assert entries == profile['ramdisk']['exact_entries'] and len(entries) == 22
    _, before, _ = dt.parse(boot.ungzip(builder.COMPILED.read_bytes())[1])
    _, after, _ = dt.parse(k[512 + 7632565:])
    changes = sorted([node, prop] for node in before.keys() | after.keys()
                     for prop in before.get(node, {}).keys() | after.get(node, {}).keys()
                     if before.get(node, {}).get(prop) != after.get(node, {}).get(prop))
    assert changes == profile['kernel']['permitted_dt_property_changes']
    chosen = after['/chosen']
    assert int.from_bytes(chosen['linux,initrd-start'], 'big') == 0x44000000
    assert int.from_bytes(chosen['linux,initrd-end'], 'big') == 0x4411f7b0
    assert [x for x in chosen['bootargs'].rstrip(b'\0').split() if x.startswith(b'initrd=')] == [b'initrd=0x44000000,0x11f7b0']
    oldh, oldk, oldr, _ = boot.parse_image(builder.OLD.read_bytes())
    assert oldr == r and oldk[512:512 + 7632565] == k[512:512 + 7632565]
    receipt = dict(status='BYTE_IDENTICAL_METADATA_REPRODUCTION', image_sha256=sha(data),
                   image_bytes=len(data), padded_sha256=sha(data + bytes(16740352-len(data))),
                   manifest_byte_identical=True, header_cmdline_bytes=len(h[64:576].split(b'\0')[0]),
                   entire_wrapped_ramdisk_unchanged=True, compressed_image_unchanged=True,
                   cpio_entries_verified=len(entries), dt_changes=changes,
                   initrd_start='0x44000000', initrd_end='0x4411f7b0', builder_sha256=BUILDER_SHA,
                   device_operations=0, physical_boot_proven=False, hardware_ready=False)
    (out / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    print(json.dumps(reproduce(parser.parse_args().out), indent=2))
