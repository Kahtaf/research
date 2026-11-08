"""One local package/preservation check using the existing format helpers."""
from pathlib import Path
import ast
import difflib
import json
import struct
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT.parent
KERNEL = WORK / '2026-11-07-asus-early-watchdog-handoff'
LOGGER = WORK / '2026-11-07-asus-stock-usb-reporter-failure-log'
INSTALLER = WORK / '2026-11-07-asus-stock-legacy-ram-usb-reporter'
CURRENT = '80270c24e310b5dd2a8e1e9e21b35a2f3d39c87dc2db25271d97b7d85da733eb'


def boundary(event, args):
    if event == 'open':
        path = str(args[0])
        assert not any(s in path for s in ('/private/', '/device-backup/', 'root_shell_wifi.py', 'mtk-su-mirror-b', '/dev/')), path
    if event.startswith(('subprocess.', 'socket.')) or event in ('os.system', 'os.posix_spawn'):
        raise RuntimeError('Local packaging cannot launch processes or use network: ' + event)


sys.addaudithook(boundary)
sys.path.insert(0, str(ROOT / 'source'))
import bootformat as b
import fdt


def record(data):
    return dict(bytes=len(data), sha256=b.sha(data))


def block(source, name):
    node = next(n for n in ast.parse(source).body if getattr(n, 'name', None) == name)
    return ''.join(source.splitlines(True)[node.lineno - 1:node.end_lineno])


def offsets(before, after):
    assert len(before) == len(after)
    return [i for i, (a, z) in enumerate(zip(before, after)) if a != z]


def main():
    attempt = ROOT / 'evidence/package-attempt.json'
    with attempt.open('x') as out:
        json.dump(dict(mode='ONE_LOCAL_PACKAGE_PRESERVATION_CHECK', device=False, compile=False), out)
        out.write('\n')
    original = (KERNEL / 'artifacts/candidate.img').read_bytes()
    donor = (LOGGER / 'artifacts/candidate.img').read_bytes()
    compiled = (KERNEL / 'artifacts/Image.gz-dtb').read_bytes()
    config = (KERNEL / 'artifacts/resolved.config').read_bytes()
    assert b.sha(original) == 'c83a4465dd209d7c2979b7b156e9d5bd8f350d81f121fa29e51579871e3a2cb4'
    assert b.sha(donor) == 'cd3cf35840129247e93b7df899d8948d811745c48e156935f9bcdd937dee0dd2'
    assert b.sha(compiled) == 'a49b87313d35d803e3ffaa2be2c60a3c678ccbc46efd5831651d2bd44ae4ee03'
    assert b.sha(config) == '708a88175ea777c09410000dfe5cf562ccbf764955eb9deaadda7326d0a966e1'
    header, kernel, oldram, tail = b.parse_image(original)
    _, _, ram, donor_tail = b.parse_image(donor)
    assert not tail and not donor_tail
    init = (LOGGER / 'artifacts/init').read_bytes()
    assert b.sha(init) == 'f410df21053fcac5f418c7d64749f19bae7921e5cc13f5c37fe5f9e99268752d'
    cp, extra = b.ungzip(ram[512:])
    entries = b.parse_cpio(cp)
    assert not extra and set(entries) == {'init', 'dev', 'proc', 'sys', 'config', 'ram'}
    assert entries['init'] == (0o100755, 0, 0, init)
    assert ram == (LOGGER / 'artifacts/ramdisk.wrapped').read_bytes()
    elf = b.elf_static(init)
    for marker in (b'ASUS-RAM-FAILLOG-20261107-R1', b'9342cbf1-3bf0-44d4-b655-a1ca30146a99', b'P499342cbf13bf044d4b655', b'ASUS-PID1:%s', b'PROBE   TXT', b'udc.bind'):
        assert marker in init, marker
    source = (LOGGER / 'source/init.c').read_bytes()
    assert b.sha(source) == 'c559ab35f75761bcd7a4e9c96154d2ee99453d80d9d3222fbe85d3d1cef86895'
    assert b'alarm(60)' in source and b'end.tv_sec+=60' in source

    raw, dt = b.ungzip(kernel[512:])
    compiled_raw, compiled_dt = b.ungzip(compiled)
    stream = kernel[512:-len(dt)]
    assert raw == compiled_raw and stream == compiled[:-len(compiled_dt)]
    # Pinned prior package contract: 4.9 payload loads at 0x44000000;
    # chosen length excludes the MTK wrapper. Do not import donor FDT/header.
    contract = json.loads((KERNEL / 'evidence/packaging-receipt.json').read_text())
    assert record(original) == contract['image']
    assert record(compiled) == contract['compiled_Image_gz_dtb']
    assert record(config) == contract['config']
    assert record(stream) == contract['compressed_Image']
    assert record(raw) == contract['decompressed_Image']
    assert record(dt) == contract['dt_after']
    h, nodes, tokens = fdt.parse(dt)
    chosen = nodes['/chosen']
    start = int.from_bytes(chosen['linux,initrd-start'], 'big')
    oldend = int.from_bytes(chosen['linux,initrd-end'], 'big')
    oldlen = struct.unpack_from('<I', oldram, 4)[0]
    payload_len = struct.unpack_from('<I', ram, 4)[0]
    assert oldlen == len(oldram) - 512 and payload_len == len(ram) - 512
    assert start == int(contract['initrd_start'], 16) == 0x44000000
    assert oldend == int(contract['initrd_end'], 16) == start + oldlen
    assert not any(arg.startswith(b'initrd=') for arg in chosen['bootargs'].rstrip(b'\0').split())
    assert chosen['bootargs'].rstrip(b'\0') == header[64:576].rstrip(b'\0') == contract['cmdline'].encode()
    newend = start + payload_len
    newdt = bytearray(dt)
    pos, changed = h[2], 0
    for token, node, name, value, encoded in tokens:
        if (token, node, name) == (3, '/chosen', 'linux,initrd-end'):
            assert len(value) == 4
            newdt[pos + 12:pos + 16] = newend.to_bytes(4, 'big')
            changed += 1
        pos += len(encoded)
    assert changed == 1
    newdt = bytes(newdt)
    expected = {n: dict(p) for n, p in nodes.items()}
    expected['/chosen']['linux,initrd-end'] = newend.to_bytes(4, 'big')
    nh, newnodes, newtokens = fdt.parse(newdt)
    assert nh == h and newnodes == expected
    for old, new in zip(tokens, newtokens):
        if old != new:
            assert old[:3] == new[:3] == (3, '/chosen', 'linux,initrd-end')
            assert old[4][:12] == new[4][:12] and old[4][16:] == new[4][16:]
    newkernel = b.wrap(kernel, stream + newdt)
    assert newkernel[:512] == kernel[:512] and len(newkernel) == len(kernel)
    image = b.make_image(header, newkernel, ram)
    full = image + bytes(b.PARTITION_SIZE - len(image))
    artifacts = dict(zip(('candidate.img', 'candidate.p10.raw', 'ramdisk.wrapped', 'init', 'Image.gz-dtb', 'resolved.config'), (image, full, ram, init, compiled, config)))
    for name, value in artifacts.items():
        (ROOT / 'artifacts' / name).write_bytes(value)
    (ROOT / 'source/init.c').write_bytes(source)
    ah, ak, ar, ax = b.parse_image((ROOT / 'artifacts/candidate.img').read_bytes())
    ar_raw, ar_dt = b.ungzip(ak[512:])
    assert not ax and ar == ram and ar_raw == raw and ar_dt == newdt
    assert ak[512:-len(ar_dt)] == stream
    assert (ROOT / 'artifacts/candidate.p10.raw').read_bytes() == full
    assert set(offsets(header, ah)) <= set(range(16, 20)) | set(range(576, 608))
    assert ah[:16] == header[:16] and ah[20:576] == header[20:576] and ah[608:] == header[608:]

    original_installer = (INSTALLER / 'source/install.py').read_text()
    edits = {
        "IMAGE_SHA='dc0b98e66798e3abc019f454921b1c84ff3ce58e356e26d0785e05b7714d3427'": f"IMAGE_SHA='{b.sha(image)}'",
        f"FULL_SHA='{CURRENT}'": f"FULL_SHA='{b.sha(full)}'",
        'len(image)==7745536': f'len(image)=={len(image)}',
        "profile='exact-stock-3.18.35-legacy-ram-usb-pid1-reporter-r1'": "profile='exact-linux49-unchanged-kernel-configfs-failure-log-r1'",
    }
    preimages = next(line for line in original_installer.splitlines() if line.startswith('INSTALL_PREIMAGES='))
    assert CURRENT not in preimages
    edits[preimages] = preimages[:-1] + f",'{CURRENT}')"
    installer = original_installer
    for old, new in edits.items():
        assert installer.count(old) == 1
        installer = installer.replace(old, new)
    restored = installer
    for old, new in reversed(list(edits.items())):
        assert restored.count(new) == 1
        restored = restored.replace(new, old)
    assert restored == original_installer
    for name in ('execute', 'Transport', 'Guard'):
        assert block(installer, name) == block(original_installer, name)
    (ROOT / 'source/install.py').write_text(installer)
    (ROOT / 'source/install.diff').write_text(''.join(difflib.unified_diff(original_installer.splitlines(True), installer.splitlines(True), fromfile='stock-legacy/source/install.py', tofile='linux49-failure-log/source/install.py')))
    helpers = {}
    for name in ('bootformat.py', 'fdt.py', 'adb', 'legacy_adb.py'):
        value = (ROOT / 'source' / name).read_bytes()
        assert value == (INSTALLER / 'source' / name).read_bytes()
        helpers[name] = record(value)
    receipt = dict(
        status='LOCAL_PACKAGED_ONE_PRESERVATION_CHECK_PASSED_NO_PHYSICAL_OR_FULLOS_GO',
        candidate=record(image), full_p10=record(full),
        inputs=dict(kernel_candidate=record(original), logger_candidate=record(donor), compiled_Image_gz_dtb=record(compiled), config=record(config), init=record(init), init_source=record(source)),
        compressed_Image=record(stream), raw_Image=record(raw), wrapped_ramdisk=record(ram), elf=elf,
        dt_before=record(dt), dt_after=record(newdt), wrapped_kernel_before=record(kernel), wrapped_kernel_after=record(newkernel),
        initrd=dict(contract='Pinned 4.9 source package and packaging-receipt.json, never donor stock geometry', payload_start=f'0x{start:08x}', old_payload_bytes=oldlen, new_payload_bytes=payload_len, old_end_exclusive=f'0x{oldend:08x}', new_end_exclusive=f'0x{newend:08x}', excluded_MTK_wrapper_bytes=512),
        preservation=dict(compressed_Image_byte_identical=True, raw_Image_byte_identical=True, config_byte_identical=True, entire_donor_wrapped_ramdisk_byte_identical=True, compiled_init_byte_identical=True, hardware_DT_and_all_properties_except_chosen_initrd_end_byte_identical=True, chosen_start_and_args_byte_identical=True, header_cmdline_load_addresses_page_and_all_except_ramdisk_size_ID_byte_identical=True, kernel_wrapper_byte_identical=True, execute_Transport_Guard_byte_identical=True, helpers_and_adapters_byte_identical=helpers),
        deltas=dict(dt_only_property='/chosen/linux,initrd-end', dt_changed_byte_offsets=offsets(dt, newdt), wrapped_kernel_changed_byte_offsets=offsets(kernel, newkernel), header_changed_byte_offsets=offsets(header, ah), old_wrapped_ramdisk_bytes=len(oldram), new_wrapped_ramdisk_bytes=len(ram), old_candidate_bytes=len(original), new_candidate_bytes=len(image), android_ID_before=header[576:608].hex(), android_ID_after=ah[576:608].hex(), alignment_and_p10_tail='Required zero alignment and full partition padding regenerated'),
        installer=dict(source=record(installer.encode()), base=record(original_installer.encode()), substitutions=5, allowed_changes=['compact hash', 'full p10 hash', 'compact length', 'profile', 'append current preimage'], only_added_preimage=CURRENT, supplied_preimage_not_freshly_observed=True, all_original_preimages_preserved=True),
        helper=dict(backend='existing CONFIGFS error logging, not stock-only legacy', run_id='9342cbf1-3bf0-44d4-b655-a1ca30146a99', serial='P499342cbf13bf044d4b655', marker='ASUS-RAM-FAILLOG-20261107-R1', product='ASUS-PID1:<actual uname.release>', RAM_FAT_readonly=True, nominal_reboot_seconds=60, edits=False, compile=False),
        scope=dict(local_only=True, device=False, network=False, SSH=False, private_inputs=False, compile=False, kernel_changes=False, install=False, reboot=False, broad_tests=False, delegation=False),
        limitation='Static package preservation only. No helper execution or live validation; isolated PLAN is separate. One bounded parent physical trial only, no fullOS GO. If no usable evidence, stop variants and report early-boot trace blocker.',
    )
    (ROOT / 'evidence/packaging-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({k: receipt[k] for k in ('status', 'candidate', 'full_p10', 'initrd', 'deltas')}, indent=2))


if __name__ == '__main__':
    main()
