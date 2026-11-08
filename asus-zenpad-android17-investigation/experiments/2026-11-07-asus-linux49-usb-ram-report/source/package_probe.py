#!/usr/bin/env python3
"""Offline RAM-only configfs specialization; no kernel compilation or device I/O."""
from pathlib import Path
import ast
import difflib
import gzip
import json
import struct
import bootformat as b
from fdt import parse

ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT.parent / '2026-11-07-asus-linux49-silent-single-cpu-probe'
BASE_SHA = '827d338c1733665c5adb40daa4a20505ec9ca7e2e586decd6069e2299bf4e062'
BASE_FULL = 'ad32e78548ec22d03685839858bcbccd163465125d4fe7c6b68f86dd19f65982'
CMD = b'androidboot.selinux=permissive bootopt=64S3,32N2,64N2 build_version=3 console=null maxcpus=1'


def record(data):
    return dict(bytes=len(data), sha256=b.sha(data))


def block(source, name):
    node = next(n for n in ast.parse(source).body if getattr(n, 'name', None) == name)
    return ''.join(source.splitlines(True)[node.lineno - 1:node.end_lineno])


def main():
    basepath = ROOT / 'inputs/base.img'
    if not basepath.exists():
        basepath = OLD / 'artifacts/candidate.img'
    old = basepath.read_bytes()
    assert len(old) == 8044544 and b.sha(old) == BASE_SHA
    previous_full = old + bytes(b.PARTITION_SIZE - len(old))
    assert b.sha(previous_full) == BASE_FULL
    prior_fullpath = OLD / 'artifacts/candidate.p10.raw'
    if prior_fullpath.exists():
        assert prior_fullpath.read_bytes() == previous_full
    header, kernel, oldram, extra = b.parse_image(old)
    assert not extra and header[64:576].split(b'\0')[0] == CMD
    raw, dt = b.ungzip(kernel[512:])
    stream = kernel[512:-len(dt)]
    assert b.sha(raw) == '43ee0529e371575bfaddb9de392b77a2279cb44bc60649fcd8d9a88b6e613b09'
    assert b.sha(stream) == '6e445d5000ad1d8dba7dd947945f2db417c45800a6036b995340b9ffc3b57b6d'
    init = (ROOT / 'artifacts/init').read_bytes()
    elf = b.elf_static(init)
    run = json.loads((ROOT / 'source/run.json').read_text())
    assert run['run_id'].encode() in init and run['usb_serial'].encode() in init
    assert b'ASUS-PID1:%s' in init and b'PROBE   TXT' in init
    entries = {n: (0o40755, 0, 0, b'') for n in ['dev', 'proc', 'sys', 'config', 'ram']}
    entries['init'] = (0o100755, 0, 0, init)
    cp = b.make_cpio(entries)
    assert b.parse_cpio(cp) == entries
    gz = bytearray(gzip.compress(cp, compresslevel=9, mtime=0)); gz[9] = 255
    ram = b.wrap(oldram, bytes(gz))
    h, nodes, tokens = parse(dt)
    assert nodes['/chosen']['bootargs'] == CMD + b'\0'
    assert nodes['/chosen']['linux,initrd-start'] == bytes.fromhex('44000000')
    assert nodes['/chosen']['linux,initrd-end'] == bytes.fromhex('4404e898')
    end = struct.pack('>I', 0x44000000 + len(ram))
    changed = 0; content = bytearray()
    for kind, node, name, value, token in tokens:
        if kind == 3 and node == '/chosen' and name == 'linux,initrd-end':
            assert len(value) == len(end) == 4
            token = token[:12] + end
            changed += 1
        content += token
    assert changed == 1 and len(content) == h[9]
    newdt = dt[:h[2]] + content + dt[h[3]:]
    expected = {n: dict(v) for n, v in nodes.items()}
    expected['/chosen']['linux,initrd-end'] = end
    assert parse(newdt)[1] == expected
    newkernel = b.wrap(kernel, stream + newdt)
    image = b.make_image(header, newkernel, ram)
    full = image + bytes(b.PARTITION_SIZE - len(image))
    (ROOT / 'artifacts/candidate.img').write_bytes(image)
    # The padded artifact remains on the builder; never fetched by remote.py.
    if (ROOT / 'inputs/base.img').exists():
        (ROOT / 'artifacts/candidate.p10.raw').write_bytes(full)
    ah, ak, ar, ax = b.parse_image((ROOT / 'artifacts/candidate.img').read_bytes())
    araw, adt = b.ungzip(ak[512:]); acp, remainder = b.ungzip(ar[512:])
    assert not ax and not remainder and b.parse_cpio(acp) == entries
    assert ak[512:-len(adt)] == stream and araw == raw and adt == newdt
    assert ak[:512] == kernel[:512] and ar[:4] == oldram[:4] and ar[8:512] == oldram[8:512]
    assert ah[:16] == header[:16] and ah[20:576] == header[20:576] and ah[608:] == header[608:]

    prior_installer = ROOT / 'inputs/install.py'
    if not prior_installer.exists():
        prior_installer = OLD / 'source/install.py'
    original = prior_installer.read_text()
    installer = original
    edits = {
        f"IMAGE_SHA='{BASE_SHA}'": f"IMAGE_SHA='{b.sha(image)}'",
        f"FULL_SHA='{BASE_FULL}'": f"FULL_SHA='{b.sha(full)}'",
        "len(image)==8044544": f"len(image)=={len(image)}",
        "'631cebb6df7be4b08edb713c976799ac60b4552e2caa3d4f1ea15b11a37610b9')":
        f"'631cebb6df7be4b08edb713c976799ac60b4552e2caa3d4f1ea15b11a37610b9','{BASE_FULL}')",
    }
    for old_text, new_text in edits.items():
        assert installer.count(old_text) == 1
        installer = installer.replace(old_text, new_text)
    for name in ['execute', 'Transport']:
        assert block(original, name) == block(installer, name)
    (ROOT / 'source/install.py').write_text(installer)
    (ROOT / 'source/install.diff').write_text(''.join(difflib.unified_diff(
        original.splitlines(True), installer.splitlines(True), fromfile='silent-single-cpu/source/install.py', tofile='source/install.py')))

    # Small static admission check: standard floppy geometry and attach ordering.
    source = (ROOT / 'source/init.c').read_text()
    assert 2880 * 512 == 1440 * 1024
    assert (1 + 2 * 9 + (224 * 32 // 512)) * 512 == 16896
    clusters = 2880 - 33
    assert clusters < 4085 and ((clusters + 2) * 3 + 1) // 2 <= 9 * 512
    ordered = ['put(LUN "ro","1")', 'put(LUN "file",RAMFILE)', 'put(G "UDC",udc)']
    assert [source.index(s) for s in ordered] == sorted(source.index(s) for s in ordered)
    assert source.count(ordered[1]) == 1 and 'S_ISREG(st.st_mode)' in source and 'fs.f_type!=TMPFS_MAGIC' in source
    assert not any(s in source for s in ['mmcblk', 'mknod(', 'system(', 'execve(', 'socket('])
    assert 'getpid()!=1||uname(&u)' in source
    manifest = dict(status='OFFLINE_PACKAGED_NO_PHYSICAL_GO', **run,
        usb=dict(vid='0x0b05', pid='0x4a49', product_format='ASUS-PID1:<actual uname.release>',
                 manufacturer='ASUS RAM PID1 Diagnostic', function='mass_storage.usb0',
                 udc_selection='exactly one actual /sys/class/udc entry; absence retry at most 10s',
                 expected_parent_udc='musb-hdrc; never hardcoded'),
        image=record(image), full_p10=record(full), init=record(init), elf=elf,
        source=record(source.encode()), input_image=record(old), input_full_p10=record(previous_full),
        compressed_Image=record(stream), decompressed_Image=record(raw),
        wrapped_ramdisk=record(ram), dt_before=record(dt), dt_after=record(adt),
        header_fields=list(struct.unpack_from('<10I', ah, 8)), android_id=ah[576:608].hex(),
        cmdline=CMD.decode(), initrd_start='0x44000000', initrd_end=f'0x{0x44000000+len(ram):08x}',
        preservation=dict(compiled_Image_byte_equal=True, compressed_Image_byte_equal=True,
            only_dt_change='/chosen/linux,initrd-end', header_only_ramdisk_size_and_id_changed=True,
            original_load_addresses_page_and_kernel_wrapper_preserved=True,
            execute_and_Transport_byte_equal=True, installer_literal_replacements=4),
        fat=dict(bytes=1440*1024, type='FAT12', sector_bytes=512, total_sectors=2880,
            fats=2, sectors_per_fat=9, root_entries=224, data_offset=16896, clusters=clusters,
            report='PROBE.TXT', fields=['run_id','pid1','sysname','release','version','machine','status'],
            backing='/ram/probe.img', required_backing_type='single-link regular file on fresh tmpfs',
            read_only_before_attachment_and_binding=True, host_write_expected='SCSI DATA PROTECT / write protected'),
        lifecycle_seconds=60, watchdog='SIGALRM reboot attempt from PID1 entry; monotonic deadline includes setup',
        config_basis='parent supplied exact e9 built-in USB_CONFIGFS / MASS_STORAGE / F_MASS_STORAGE / F_FS; vendor MTK UDC',
        physical_validation=False, automatic_return_proven=False, device_operations=0,
        native_android_operations=0, kernel_compilation=False,
        runtime_hardware_note='Kernel hardware initialization still occurs normally; zero hardware effects is not claimed')
    (ROOT / 'evidence/manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(dict(image=record(image), full_p10=record(full), **run)))


if __name__ == '__main__':
    main()
