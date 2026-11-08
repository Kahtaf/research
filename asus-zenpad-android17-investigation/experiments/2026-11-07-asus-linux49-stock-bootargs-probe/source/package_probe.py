#!/usr/bin/env python3
"""One offline bootargs-only specialization of the existing packaged 4.9 probe."""
from pathlib import Path
import ast
import difflib
import json
import shutil
import struct
import bootformat as b
from fdt import parse

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT.parent
OLD = WORK / '2026-11-07-asus-sd-media-flag-probe'
CONTROL = WORK / '2026-11-07-asus-stock-kernel-sd-control'
CMD = b'androidboot.selinux=permissive bootopt=64S3,32N2,64N2 build_version=3'
FAILED = b'bootopt=64S3,32N2,64N2 build_version=3 androidboot.boot_devices=soc/11230000.mmc enforcing=1'
STOCK_FULL = '4b564d404bc13b20ba44790733a37010fe0677bfced235de2b334c3bff08fa19'


def record(data):
    return dict(bytes=len(data), sha256=b.sha(data))


def patch_bootargs(dt):
    h, nodes, tokens = parse(dt)
    old = nodes['/chosen']['bootargs']
    assert old.endswith(FAILED + b'\0')
    prefix = old[:-len(FAILED + b'\0')]
    new = prefix + CMD + b'\0'
    stream = bytearray()
    seen = 0
    for kind, node, name, value, raw in tokens:
        if kind == 3 and node == '/chosen' and name == 'bootargs':
            off = struct.unpack_from('>I', raw, 8)[0]
            stream += struct.pack('>III', 3, len(new), off) + new + bytes(-len(new) % 4)
            seen += 1
        else:
            stream += raw
    assert seen == 1
    # Preserve the original strings block and all trailing DT padding verbatim.
    tail = dt[h[3]:]
    after_h = list(h)
    after_h[3] = h[2] + len(stream)
    after_h[9] = len(stream)
    after_h[1] = after_h[3] + len(tail)
    result = struct.pack('>10I', *after_h) + dt[40:h[2]] + stream + tail
    expected = {n: dict(p) for n, p in nodes.items()}
    expected['/chosen']['bootargs'] = new
    assert parse(result)[1] == expected
    assert result[40:h[2]] == dt[40:h[2]]
    assert result[after_h[3]:] == tail
    return result, prefix


def block(source, name):
    lines = source.splitlines(keepends=True)
    node = next(n for n in ast.parse(source).body if getattr(n, 'name', None) == name)
    return ''.join(lines[node.lineno - 1:node.end_lineno])


def main():
    old = (OLD / 'artifacts/candidate.img').read_bytes()
    control = (CONTROL / 'artifacts/candidate.img').read_bytes()
    control_full = (CONTROL / 'artifacts/candidate.p10.raw').read_bytes()
    assert record(old) == dict(bytes=8044544, sha256='999a575cc3dcb20b92f45a8281de19d1d452ad304836b5dded93422aca9d2510')
    assert record(control) == dict(bytes=7798784, sha256='eccfc87f28169bee14d0675f6ad31335f832ab25db46b013b03a06109b0df13d')
    assert control_full == control + bytes(b.PARTITION_SIZE - len(control))
    assert b.sha(control_full) == STOCK_FULL
    header, kernel, ramdisk, extra = b.parse_image(old)
    control_header, _, control_ramdisk, control_extra = b.parse_image(control)
    assert not extra and not control_extra
    assert control_header[64:576].split(b'\0')[0] == CMD
    assert header[64:576].split(b'\0')[0] == FAILED
    assert not any(header[608:1632]) and not any(control_header[608:1632])
    assert ramdisk == control_ramdisk
    assert b.sha(ramdisk) == '51a6d8deb3368c8b8a10d6d730ca21c6b157fda5f940d5ba7cdcb2d2a6788e46'
    raw, dt = b.ungzip(kernel[512:])
    stream = kernel[512:-len(dt)]
    newdt, prefix = patch_bootargs(dt)
    newkernel = b.wrap(kernel, stream + newdt)
    newheader = bytearray(header)
    newheader[64:576] = CMD + bytes(512 - len(CMD))
    image = b.make_image(newheader, newkernel, ramdisk)
    full = image + bytes(b.PARTITION_SIZE - len(image))
    (ROOT / 'artifacts/candidate.img').write_bytes(image)
    (ROOT / 'artifacts/candidate.p10.raw').write_bytes(full)

    # Check the actual emitted containers, not a surrogate or a recompiled input.
    actual = (ROOT / 'artifacts/candidate.img').read_bytes()
    ah, ak, ar, at = b.parse_image(actual)
    araw, adt = b.ungzip(ak[512:])
    assert actual == image and not at and ar == ramdisk
    assert ak[512:-len(adt)] == stream and araw == raw and adt == newdt
    assert ak[:4] == kernel[:4] and ak[8:512] == kernel[8:512]
    assert ah[:8] == header[:8] and ah[12:64] == header[12:64] and ah[608:] == header[608:]
    assert ah[64:576] == CMD + bytes(512 - len(CMD))
    before, after = parse(dt)[1], parse(adt)[1]
    changes = sorted([n, p] for n in before.keys() | after.keys()
                     for p in before.get(n, {}).keys() | after.get(n, {}).keys()
                     if before.get(n, {}).get(p) != after.get(n, {}).get(p))
    assert changes == [['/chosen', 'bootargs']]
    for key in ('linux,initrd-start', 'linux,initrd-end'):
        assert before['/chosen'][key] == after['/chosen'][key]
    assert (ROOT / 'artifacts/candidate.p10.raw').read_bytes() == full

    original = (CONTROL / 'source/install.py').read_text()
    edits = {
        "IMAGE_SHA='eccfc87f28169bee14d0675f6ad31335f832ab25db46b013b03a06109b0df13d'": f"IMAGE_SHA='{b.sha(image)}'",
        f"FULL_SHA='{STOCK_FULL}'": f"FULL_SHA='{b.sha(full)}'",
        "'7161898f7858c5eb2887a4589fce5a62d4b2d556e1413e36e4e53c3cd8431b09')": f"'7161898f7858c5eb2887a4589fce5a62d4b2d556e1413e36e4e53c3cd8431b09','{STOCK_FULL}')",
        'len(image)==7798784': f'len(image)=={len(image)}',
    }
    installer = original
    for old_text, new_text in edits.items():
        assert installer.count(old_text) == 1
        installer = installer.replace(old_text, new_text)
    for name in ('execute', 'Transport'):
        assert block(original, name) == block(installer, name)
    (ROOT / 'source/install.py').write_text(installer)
    (ROOT / 'source/install.diff').write_text(''.join(difflib.unified_diff(
        original.splitlines(True), installer.splitlines(True),
        fromfile='stock-kernel-sd-control/source/install.py', tofile='source/install.py')))
    copies = {}
    for name in ('adb', 'legacy_adb.py'):
        src, dst = CONTROL / 'source' / name, ROOT / 'source' / name
        shutil.copy2(src, dst)
        assert src.read_bytes() == dst.read_bytes()
        copies[name] = record(dst.read_bytes())
    cp, remainder = b.ungzip(ar[512:])
    assert not remainder
    init = b.parse_cpio(cp)['init'][3]
    assert b'dbbb6afb-dd70-4c35-961e-9c977d7164a8\n' in init
    receipt = dict(
        status='LOCAL_PACKAGED_NO_PHYSICAL_LINUX49_PROOF',
        inputs=dict(failed_linux49=record(old), working_stock_control=record(control), working_stock_control_full_p10=record(control_full)),
        image=record(actual), full_p10=record(full),
        android_container='Android boot image v0, 2048-byte pages; MTK 512-byte KERNEL and RECOVERY wrappers; gzip Image followed by FDT',
        header_fields=list(struct.unpack_from('<10I', ah, 8)), android_id_hex=ah[576:608].hex(),
        header_cmdline=CMD.decode(), chosen_bootargs=after['/chosen']['bootargs'].rstrip(b'\0').decode(),
        unchanged_chosen_prefix=prefix.decode(), dt_changes=changes,
        initrd_start_hex=after['/chosen']['linux,initrd-start'].hex(), initrd_end_hex=after['/chosen']['linux,initrd-end'].hex(),
        compressed_Image=record(stream), decompressed_Image=record(araw), wrapped_ramdisk=record(ar), init=record(init),
        wrapped_kernel_before=record(kernel), wrapped_kernel_after=record(ak), dt_before=record(dt), dt_after=record(adt),
        preservation=dict(compressed_Image_byte_equal=True, decompressed_Image_byte_equal=True,
                          wrapped_ramdisk_byte_equal=True, initrd_bounds_byte_equal=True,
                          dt_only_bootargs_changed=True, wrapper_only_length_changed=True,
                          header_only_kernel_size_cmdline_id_changed=True,
                          execute_and_Transport_byte_equal=True, installer_four_literal_replacements=True,
                          exact_adapter_copies=copies),
        run_id='dbbb6afb-dd70-4c35-961e-9c977d7164a8', report='PROBE.TXT', lifecycle_seconds=60,
        sd_paths=['/sys/class/block/mmcblk1', '/sys/class/block/mmcblk1p1', '/dev/sd-report', '/sd'],
        parent_reported_stock_evidence=dict(report_bytes=175, report_sha256='a258dec186b5f27912d666c9624e8d640da5a815328b23870482ff4a630f9483',
            receipt='2026-11-07-asus-stock-kernel-sd-control/evidence/report-after-trial.json',
            uname='Linux 3.18.35 #1 SMP PREEMPT Thu Aug 9 12:33:25 CST 2018 / aarch64', independently_read=False),
        compilation=False, hardware_contact=False, physical_linux49_boot_proven=False, flash_go=False,
        android17_enforcing_target_and_product_sources_unchanged=True)
    (ROOT / 'evidence/packaging-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    owned = sum(p.stat().st_size for p in ROOT.rglob('*') if p.is_file())
    assert owned < 48 * 1024 * 1024
    print(json.dumps(dict(image=record(image), full_p10=record(full), owned_bytes=owned)))


if __name__ == '__main__':
    main()
