#!/usr/bin/env python3
"""Future full BOOT metadata replacement. Default PLAN_ONLY; no device operations."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'probe'))

from bootformat import sha, pad, wrap, boot_id, ungzip, parse_cpio, PARTITION_SIZE
from fdt import parse
from boot_memory import check_memory
from lk_contract import need, narrow_header, chosen_dt, kernel_config, RAMDISK_START, model_lk_gzip

if not __debug__:
    raise RuntimeError('Do not use optimized Python: inherited bounded parsers require assertions')


def components(data):
    need(2048 <= len(data) <= PARTITION_SIZE and data[:8] == b'ANDROID!', 'Invalid Android v0 image')
    ks, ka, rs, ra, ss, sa, ta, page = struct.unpack_from('<8I', data, 8)
    need((ka, ra, ss, ta, page) == (0x40080000, RAMDISK_START, 0, 0x4e000000, 2048), 'Unsupported header geometry')
    need(sa in (0, 0x40f00000) and struct.unpack_from('<I', data, 40)[0] == 0, 'Unsupported header version/second')
    need(ks > 0 and rs > 0, 'Empty component')
    ro = page + (ks + page - 1) // page * page
    k, ram = data[page:page + ks], data[ro:ro + rs]
    need(len(k) == ks and len(ram) == rs, 'Truncated component')
    need(data == data[:page] + pad(k) + pad(ram), 'Nonzero padding or trailing data')
    need(data[576:608] == boot_id(k, ram), 'Android component ID mismatch')
    need(not any(data[608:1632]), 'Extended cmdline unsupported')
    need(not any(data[1632:2048]), 'Unreviewed header-page tail')
    field = data[64:576]; cmd, nul, tail = field.partition(b'\0')
    need(nul and not any(tail), 'Noncanonical cmdline field')
    return data[:page], k, ram, cmd


def wrapper_templates():
    provenance = json.loads((ROOT / 'evidence/stock-wrapper-provenance.json').read_text())
    values = []
    for label, name in [('kernel', b'KERNEL'), ('ramdisk', b'ROOTFS')]:
        value = (ROOT / 'inputs' / ('stock-' + label + '-wrapper.bin')).read_bytes()
        need(len(value) == 512 and sha(value) == provenance[label + '_wrapper_sha256'], 'Wrapper provenance mismatch')
        need(value[:4] == bytes.fromhex('88168858') and value[8:40].split(b'\0')[0] == name, 'Wrong normal-BOOT wrapper')
        values.append(value)
    return *values, provenance


def validate_ramdisk(ram, synthetic):
    raw, tail = ungzip(ram)
    need(not tail, 'Extra gzip member, bootconfig or trailer forbidden')
    entries = parse_cpio(raw)
    marker = 'NONBOOTABLE-SYNTHETIC-FIXTURE.txt'
    if synthetic:
        need(marker in entries and 'init' not in entries, 'Synthetic fixture must be marked and have no init')
    else:
        need(marker not in entries, 'Synthetic fixture rejected for full packaging')
        need('init' in entries, 'Missing first-stage init')
        mode, uid, gid, init = entries['init']
        need(mode & 0o170000 == 0o100000 and mode & 0o111 and init[:6] == b'\x7fELF\x02\x01', 'Full BOOT requires an executable AArch64 init')
        need(len(init) >= 20 and struct.unpack_from('<H', init, 18)[0] == 183, 'init is not AArch64')
    paths = ('fstab.mt8163', 'system/etc/fstab.mt8163', 'first_stage_ramdisk/fstab.mt8163', 'first_stage_ramdisk/system/etc/fstab.mt8163')
    present = [entries[p] for p in paths if p in entries]
    need(present, 'Missing hardware fallback fstab.mt8163')
    expected_sha = '04179d23e76be8755f6452319e05cc89f2438b51fcc539cb76695c9c65c57e75'
    for mode, uid, gid, content in present:
        need(mode & 0o170000 == 0o100000 and sha(content) == expected_sha, 'Unreviewed fstab content/type')
    return {'cpio_entries': len(entries), 'fstab_sha256': expected_sha, 'synthetic_nonbootable': synthetic}


def package(data, expected_kernel, build_report, *, synthetic=False):
    need(sha(data) == build_report['boot']['sha256'], 'AOSP BOOT report hash mismatch')
    header, k, ram, original_cmd = components(data)
    need(k == expected_kernel, 'Kernel differs from qualified input')
    cmd = narrow_header(original_cmd)
    ram_report = validate_ramdisk(ram, synthetic)
    raw, dt = ungzip(k)
    need(dt, 'No appended DT')
    config = kernel_config(raw)
    newdt = chosen_dt(dt, len(ram), cmd)
    memory = check_memory(raw, newdt, len(ram))
    stream = k[:-len(dt)]
    kw, rw, provenance = wrapper_templates()
    wk, wr = wrap(kw, stream + newdt), wrap(rw, ram)
    h = bytearray(header)
    struct.pack_into('<I', h, 8, len(wk)); struct.pack_into('<I', h, 16, len(wr))
    struct.pack_into('<I', h, 28, 0x40f00000)
    h[64:576] = cmd + bytes(512 - len(cmd)); h[576:608] = boot_id(wk, wr)
    if synthetic: h[48:64] = b'NONBOOTABLE' + bytes(5)
    image = bytes(h) + pad(wk) + pad(wr)
    need(len(image) <= PARTITION_SIZE, 'BOOT partition overflow')
    # LK scans backward past the DT by 512 bytes due to the wrapped header size.
    # Check the exact staging bytes it can observe; no later accidental FDT magic allowed.
    scan = (pad(wk) + pad(wr))[512:512 + len(wk) + 4]
    inflate = model_lk_gzip(scan, len(wk), len(stream), raw)
    oh, ok, oram, ocmd = components(image)
    need(ok[512:512 + len(stream)] == stream and oram[512:] == ram, 'Compressed payload changed')
    for actual, template, name in [(ok, kw, b'KERNEL'), (oram, rw, b'ROOTFS')]:
        need(actual[:4] == template[:4] and actual[8:512] == template[8:512], 'MTK wrapper changed')
        need(struct.unpack_from('<I', actual, 4)[0] == len(actual) - 512, 'Wrapper length mismatch')
        need(actual[8:40].split(b'\0')[0] == name, 'Normal BOOT wrapper name mismatch')
    need(oram[512:514] == b'\x1f\x8b', 'LK destination must begin with gzip magic')
    chosen = parse(newdt)[1]['/chosen']
    need(int.from_bytes(chosen['linux,initrd-start'], 'big') == RAMDISK_START, 'Wrong LK DT start')
    digest = hashlib.sha256(image); digest.update(bytes(PARTITION_SIZE - len(image)))
    report = {'status': 'NONBOOTABLE_SYNTHETIC_FIXTURE' if synthetic else 'PACKAGING_VALIDATED_HARDWARE_UNTESTED',
              'aosp_boot_sha256': sha(data), 'input_kernel_sha256': sha(k),
              'image_sha256': sha(image), 'image_bytes': len(image), 'partition_bytes': PARTITION_SIZE,
              'padded_partition_sha256': digest.hexdigest(), 'header_cmdline': cmd.decode(), 'header_cmdline_bytes': len(cmd),
              'input_header_cmdline': original_cmd.decode(), 'ramdisk_start': hex(RAMDISK_START),
              'ramdisk_end': hex(RAMDISK_START + len(ram)), 'ramdisk_bytes': len(ram),
              'compressed_image_sha256': sha(stream), 'ramdisk_compressed_sha256': sha(ram),
              'compressed_kernel_unchanged': True, 'ramdisk_compressed_unchanged': True,
              'lk_gzip_semantic_model': inflate, 'dtb_sha256': sha(newdt), 'compiled_config_sha256': sha(config), 'memory_layout': memory,
              'dt_allowed_changes': ['chosen/bootargs', 'chosen/linux,initrd-start', 'chosen/linux,initrd-end'],
              'ramdisk': ram_report, 'wrapper_provenance': provenance, 'hardware_boot_validated': False,
              'asus_signature_valid': False, 'flashable_claim': False,
              'runtime_lk_properties_and_secure_monitor_verified': False}
    return image, newdt, report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for n in ('aosp-boot', 'build-report', 'kernel', 'out'): p.add_argument('--' + n, type=Path, required=True)
    p.add_argument('--mode', choices=('PLAN_ONLY', 'SYNTHETIC_FIXTURE', 'PACKAGE_UNTESTED'), default='PLAN_ONLY')
    a = p.parse_args()
    image, dt, report = package(a.aosp_boot.read_bytes(), a.kernel.read_bytes(), json.loads(a.build_report.read_text()), synthetic=a.mode == 'SYNTHETIC_FIXTURE')
    a.out.mkdir(parents=True, exist_ok=False)
    report['mode'] = a.mode
    if a.mode != 'PLAN_ONLY':
        name = 'NONBOOTABLE-SYNTHETIC-full-BOOT.img' if a.mode == 'SYNTHETIC_FIXTURE' else 'UNTESTED-sdk37-combined-boot.img'
        (a.out / name).write_bytes(image); (a.out / 'packaged.dtb').write_bytes(dt)
        report['image_file'] = name
    (a.out / 'manifest.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__': main()
