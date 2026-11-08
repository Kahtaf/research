#!/usr/bin/env python3
"""One offline package: existing UART-disabled kernel and exact RAM USB reporter."""
from pathlib import Path
import ast
import difflib
import json
import shutil
import struct
import bootformat as b
from fdt import parse

R = Path(__file__).resolve().parents[1]
W = R.parent
K = W / '2026-11-07-asus-early-uart-disabled-kernel'
U = W / '2026-11-07-asus-linux49-usb-ram-report'
CMD = b'androidboot.selinux=permissive bootopt=64S3,32N2,64N2 build_version=3 console=null maxcpus=1'
PREVIOUS = 'e965b75979e02e5514418e706f42b7874e4f72d72754864e5af0959646d2c9b0'


def rec(data):
    return dict(bytes=len(data), sha256=b.sha(data))


def block(source, name):
    node = next(n for n in ast.parse(source).body if getattr(n, 'name', None) == name)
    return ''.join(source.splitlines(True)[node.lineno-1:node.end_lineno])


def main():
    assert not (R / 'artifacts/candidate.img').exists(), 'One package only'
    current = (K / 'artifacts/candidate.img').read_bytes()
    usb = (U / 'artifacts/candidate.img').read_bytes()
    compiled = (K / 'artifacts/Image.gz-dtb').read_bytes()
    config = (K / 'artifacts/resolved.config').read_bytes()
    assert rec(current) == dict(bytes=8038400, sha256='1d406f3416e94e54219935cb76de338e10d3155fe555baad6cb7c2e38068c95d')
    assert b.sha(usb) == '6b8c2d1c41685c7592a4aa42cd809e070e8033c0226febb9137285ef4e379f5d'
    assert rec(compiled) == dict(bytes=7711217, sha256='063dad1d9cc03b1c335dd712c9fcb0c36a006e5e99ebee4577e73e669613ac2d')
    assert b.sha(config) == '708a88175ea777c09410000dfe5cf562ccbf764955eb9deaadda7326d0a966e1'
    assert b.sha(current + bytes(b.PARTITION_SIZE-len(current))) == PREVIOUS
    header, kernel, _, extra = b.parse_image(current)
    _, _, ramdisk, ux = b.parse_image(usb)
    assert not extra and not ux
    assert header[64:576] == CMD + bytes(512-len(CMD))
    raw, dt = b.ungzip(kernel[512:])
    compiled_raw, compiled_dt = b.ungzip(compiled)
    stream = kernel[512:-len(dt)]
    assert stream == compiled[:-len(compiled_dt)] and raw == compiled_raw
    cp, remainder = b.ungzip(ramdisk[512:])
    assert not remainder
    init = b.parse_cpio(cp)['init'][3]
    elf = b.elf_static(init)
    manifest = json.loads((U / 'evidence/manifest.json').read_text())
    assert rec(ramdisk) == manifest['wrapped_ramdisk']
    assert rec(init) == manifest['init'] == dict(bytes=597856, sha256='d081c46dcf40684b35ec5f16bb4238b60662dd857a7211d46241e98f96ac872b')
    run = json.loads((U / 'source/run.json').read_text())
    assert run['run_id'].encode() in init and run['usb_serial'].encode() in init
    assert b'ASUS-PID1:%s' in init and b'PROBE   TXT' in init
    payload_length = len(ramdisk)-512
    assert struct.unpack_from('<I', ramdisk, 4)[0] == payload_length
    assert len(ramdisk) == 255651 and payload_length == 0x3e4a3
    h, nodes, tokens = parse(dt)
    assert nodes['/chosen']['bootargs'] == CMD+b'\0'
    start = int.from_bytes(nodes['/chosen']['linux,initrd-start'], 'big')
    assert start == 0x44000000
    end = struct.pack('>I', start+payload_length)
    assert end.hex() == '4403e4a3'
    content = bytearray()
    changed = 0
    for kind, node, name, value, token in tokens:
        if kind == 3 and node == '/chosen' and name == 'linux,initrd-end':
            assert len(value) == 4
            token = token[:12]+end
            changed += 1
        content += token
    assert changed == 1 and len(content) == h[9]
    newdt = dt[:h[2]]+content+dt[h[3]:]
    expected = {n: dict(props) for n, props in nodes.items()}
    expected['/chosen']['linux,initrd-end'] = end
    assert parse(newdt)[1] == expected and parse(newdt)[0] == h
    assert [(t,n,p,v,r) for t,n,p,v,r in parse(newdt)[2] if not (n=='/chosen' and p=='linux,initrd-end')] == [(t,n,p,v,r) for t,n,p,v,r in tokens if not (n=='/chosen' and p=='linux,initrd-end')]
    newkernel = b.wrap(kernel, stream+newdt)
    assert newkernel[:512] == kernel[:512]
    image = b.make_image(header, newkernel, ramdisk)
    full = image+bytes(b.PARTITION_SIZE-len(image))
    (R / 'artifacts/candidate.img').write_bytes(image)
    (R / 'artifacts/candidate.p10.raw').write_bytes(full)
    (R / 'artifacts/ramdisk.wrapped').write_bytes(ramdisk)
    (R / 'artifacts/init').write_bytes(init)
    ah, ak, ar, ax = b.parse_image((R / 'artifacts/candidate.img').read_bytes())
    actual_raw, actual_dt = b.ungzip(ak[512:])
    assert not ax and ar == ramdisk and actual_raw == raw and actual_dt == newdt
    assert ak[512:-len(actual_dt)] == stream
    assert ah[:16] == header[:16] and ah[20:576] == header[20:576] and ah[608:] == header[608:]
    assert (R / 'artifacts/candidate.p10.raw').read_bytes() == full
    assert len(full) == 16740352 and not any(full[len(image):])
    original = (K / 'source/install.py').read_text()
    installer = original
    edits = {
        "IMAGE_SHA='1d406f3416e94e54219935cb76de338e10d3155fe555baad6cb7c2e38068c95d'": f"IMAGE_SHA='{b.sha(image)}'",
        f"FULL_SHA='{PREVIOUS}'": f"FULL_SHA='{b.sha(full)}'",
        'len(image)==8038400': f'len(image)=={len(image)}',
        "profile='exact-linux49-early-uart-disabled-microsd-probe'": "profile='exact-linux49-uart-fixed-ram-usb-pid1-report'",
        "'4fb2f280ba90e9e1487b3728056a67ccd4883f918cc81a1145c100a3eb999a26')": f"'4fb2f280ba90e9e1487b3728056a67ccd4883f918cc81a1145c100a3eb999a26','{PREVIOUS}')",
    }
    for old, new in edits.items():
        assert installer.count(old) == 1
        installer = installer.replace(old, new)
    for name in ['execute', 'Transport', 'Guard']:
        assert block(original, name) == block(installer, name)
    (R / 'source/install.py').write_text(installer)
    (R / 'source/install.diff').write_text(''.join(difflib.unified_diff(original.splitlines(True), installer.splitlines(True), fromfile='uart-disabled/source/install.py', tofile='source/install.py')))
    adapters = {}
    for name in ['adb', 'legacy_adb.py']:
        shutil.copy2(K / 'source' / name, R / 'source' / name)
        assert (R / 'source' / name).read_bytes() == (K / 'source' / name).read_bytes()
        adapters[name] = rec((R / 'source' / name).read_bytes())
    receipt = dict(status='PACKAGED_NO_PHYSICAL_GO', image=rec(image), full_p10=rec(full), input_current=rec(current), input_usb=rec(usb), compiled_Image_gz_dtb=rec(compiled), config=rec(config), compressed_Image=rec(stream), decompressed_Image=rec(raw), dt_before=rec(dt), dt_after=rec(newdt), wrapped_kernel=rec(ak), wrapped_ramdisk=rec(ar), compressed_ramdisk_payload=rec(ar[512:]), ramdisk_cpio=rec(cp), init=rec(init), elf=elf, **run,
        cmdline=CMD.decode(), initrd_start=hex(start), initrd_end=hex(start+payload_length),
        length_correction='Actual wrapped length 0x3e6a3 includes 512-byte MTK wrapper; actual compressed payload is 0x3e4a3. Payload+0x44000000 yields 0x4403e4a3, not supplied 0x4403e6a3.',
        header_fields=list(struct.unpack_from('<10I', ah, 8)), android_id_hex=ah[576:608].hex(), dt_changes=[['/chosen','linux,initrd-end']],
        preservation=dict(compiled_gzip_byte_equal=True, compiled_raw_Image_byte_equal=True, DT_only_initrd_end_changed=True, DT_header_reservations_strings_and_other_tokens_byte_equal=True, wrapped_ramdisk_byte_equal=True, static_init_byte_equal=True, kernel_wrapper_byte_equal=True, header_only_ramdisk_length_and_image_id_changed=True, execute_Transport_Guard_byte_equal=True, legacy_adapters=adapters, full_p10_zero_padding=True),
        only_added_known_full_preimage=PREVIOUS, parent_install_run='097b74f7-ed11-45bc-94ca-a12c547ab3d7', installer=rec(installer.encode()), installer_edits=edits,
        usb=dict(vid='0b05',pid='4a49',product='ASUS-PID1:<actual uname.release>',identity_reused_unchanged=True,fresh_host_absence_required=True),
        lifecycle_seconds=60, report='readonly tmpfs FAT12 PROBE.TXT; actual uname; no SD/eMMC mounts or block writes', kernel_compilation=False, init_compilation=False, hardware_contact=False, physical_boot_proven=False, flash_go=False)
    (R / 'evidence/packaging-receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
    print(json.dumps(dict(image=rec(image),full_p10=rec(full),initrd_end=hex(start+payload_length))))


if __name__ == '__main__':
    main()
