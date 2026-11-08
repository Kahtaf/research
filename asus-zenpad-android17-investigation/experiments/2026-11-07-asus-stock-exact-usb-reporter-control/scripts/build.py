"""Local packaging of the exact USB reporter with the known-working stock kernel."""
from pathlib import Path
import ast
import difflib
import hashlib
import json
import shutil
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT.parent
REPORTER = WORK / '2026-11-07-asus-linux49-usb-ram-report'
PRIOR = WORK / '2026-11-07-asus-early-watchdog-handoff'
STOCK = WORK / '2026-11-07-asus-stock-kernel-version-control/artifacts/original.img'
CURRENT = '81bc90ed8f8c25a291c8ffca205de94a0188b5cbab37379b3f667ad1ac42ba2d'


def boundary(event, args):
    if event == 'open':
        path = str(args[0])
        assert not any(s in path for s in ('/private/', '/device-backup/', 'root_shell_wifi.py', 'mtk-su-mirror-b', '/dev/')), path
    if event.startswith(('subprocess.', 'socket.')) or event in ('os.system', 'os.posix_spawn'):
        raise RuntimeError('Packaging cannot launch processes or use network: ' + event)


sys.addaudithook(boundary)
sha = lambda data: hashlib.sha256(data).hexdigest()
record = lambda data: dict(bytes=len(data), sha256=sha(data))


def block(source, name):
    node = next(n for n in ast.parse(source).body if getattr(n, 'name', None) == name)
    return ''.join(source.splitlines(True)[node.lineno - 1:node.end_lineno])


def changed_offsets(before, after):
    assert len(before) == len(after)
    return [i for i, (a, b) in enumerate(zip(before, after)) if a != b]


def main():
    for name in ('artifacts', 'source', 'evidence'):
        (ROOT / name).mkdir(exist_ok=True)
    copies = {}
    for name in ('bootformat.py', 'fdt.py'):
        src, dst = REPORTER / 'source' / name, ROOT / 'source' / name
        shutil.copy2(src, dst)
        assert src.read_bytes() == dst.read_bytes()
        copies[name] = record(dst.read_bytes())
    sys.path.insert(0, str(ROOT / 'source'))
    import bootformat as b
    import fdt

    stock = STOCK.read_bytes()
    reporter = (REPORTER / 'artifacts/candidate.img').read_bytes()
    assert len(stock) == 7804928 and sha(stock) == 'f0bf4834a2d3ec207590c6742d0adb4fd9a3adc9a2dab5d0ec7c28f27963b140'
    assert sha(reporter) == '6b8c2d1c41685c7592a4aa42cd809e070e8033c0226febb9137285ef4e379f5d'
    header, kernel, oldram, tail = b.parse_image(stock)
    _, _, ram, report_tail = b.parse_image(reporter)
    assert not tail and not report_tail
    assert sha(kernel) == 'd585f856946b4f4e02f95e7ef796423a046ce7c0c2a661680abd87b8b5326952'
    raw, dt = b.ungzip(kernel[512:])
    stream = kernel[512:-len(dt)]
    assert sha(raw) == 'db90ee7fff379f35ac2b0aafb11a6abee7b2c283b57d352c40ae7c6d7c35eb2a'
    assert sha(dt) == '77e2d8fbeced5a827ede6c0b8589140e9211d8dc3ca77aaa31a1dd1787a9c455'
    assert len(ram) == 255651 and sha(ram) == '51e6d1dc0acb742522c69b29355d2d77d8ba73a3597fb8ad3354fa9f0c494e49'
    payload = ram[512:]
    assert len(payload) == 255139 == 0x3e4a3
    cp, extra = b.ungzip(payload)
    entries = b.parse_cpio(cp)
    assert not extra and set(entries) == {'init', 'dev', 'ram', 'proc', 'sys', 'config'}
    init = entries['init'][3]
    assert sha(init) == 'd081c46dcf40684b35ec5f16bb4238b60662dd857a7211d46241e98f96ac872b'
    elf = b.elf_static(init)
    for marker in (b'9342cbf1-3bf0-44d4-b655-a1ca30146a99', b'P499342cbf13bf044d4b655', b'ASUS-PID1:%s', b'P49RAM', b'PROBE   TXT'):
        assert marker in init, marker

    # Stock LK skips the MTK wrapper: retain start 0x44000200, bound payload only.
    # Equal-width hex keeps property size, all FDT offsets and wrapper size exact.
    _, nodes, tokens = fdt.parse(dt)
    old_token = b'initrd=0x44000200,0x200000'
    new_token = b'initrd=0x44000200,0x03e4a3'
    assert len(old_token) == len(new_token) and dt.count(old_token) == 1
    assert nodes['/chosen']['bootargs'].split().count(old_token + b'\0') == 1
    newdt = dt.replace(old_token, new_token)
    _, newnodes, newtokens = fdt.parse(newdt)
    expected = {n: dict(p) for n, p in nodes.items()}
    expected['/chosen']['bootargs'] = nodes['/chosen']['bootargs'].replace(old_token, new_token)
    assert newnodes == expected
    assert len(tokens) == len(newtokens)
    for before, after in zip(tokens, newtokens):
        if before != after:
            assert before[:3] == after[:3] == (3, '/chosen', 'bootargs')
            assert before[4].replace(old_token, new_token) == after[4]
    newkernel = b.wrap(kernel, stream + newdt)
    assert newkernel[:512] == kernel[:512]
    assert len(newkernel) == len(kernel)
    image = b.make_image(header, newkernel, ram)
    full = image + bytes(b.PARTITION_SIZE - len(image))
    (ROOT / 'artifacts/candidate.img').write_bytes(image)
    (ROOT / 'artifacts/candidate.p10.raw').write_bytes(full)
    (ROOT / 'artifacts/ramdisk.wrapped').write_bytes(ram)
    ah, ak, ar, ax = b.parse_image((ROOT / 'artifacts/candidate.img').read_bytes())
    araw, adt = b.ungzip(ak[512:])
    assert not ax and ar == ram and araw == raw and adt == newdt
    assert ak[512:-len(adt)] == stream
    assert (ROOT / 'artifacts/candidate.p10.raw').read_bytes() == full
    allowed_header = set(range(16, 20)) | set(range(576, 608))
    header_changes = changed_offsets(header, ah)
    assert set(header_changes) <= allowed_header
    assert ah[64:576] == header[64:576]
    assert b'console=null' not in ah[64:576] and b'maxcpus=' not in ah[64:576]
    assert ah == b.make_image(header, newkernel, ram)[:2048]

    original = (PRIOR / 'source/install.py').read_text()
    edits = {
        "IMAGE_SHA='c83a4465dd209d7c2979b7b156e9d5bd8f350d81f121fa29e51579871e3a2cb4'": f"IMAGE_SHA='{sha(image)}'",
        f"FULL_SHA='{CURRENT}'": f"FULL_SHA='{sha(full)}'",
        'len(image)==7970816': f'len(image)=={len(image)}',
        "profile='exact-linux49-early-watchdog-handoff-ram-usb-pid1-report'": "profile='exact-stock-3.18.35-unchanged-ram-usb-pid1-reporter-control'",
    }
    # CURRENT formerly named the candidate, not an admitted installation preimage.
    preimages = next(line for line in original.splitlines() if line.startswith('INSTALL_PREIMAGES='))
    assert CURRENT not in preimages
    edits[preimages] = preimages[:-1] + f",'{CURRENT}')"
    installer = original
    for old, new in edits.items():
        assert installer.count(old) == 1
        installer = installer.replace(old, new)
    for name in ('execute', 'Transport', 'Guard'):
        assert block(installer, name) == block(original, name)
    (ROOT / 'source/install.py').write_text(installer)
    (ROOT / 'source/install.diff').write_text(''.join(difflib.unified_diff(
        original.splitlines(True), installer.splitlines(True),
        fromfile='2026-11-07-asus-early-watchdog-handoff/source/install.py', tofile='source/install.py')))
    adapters = {}
    for name in ('adb', 'legacy_adb.py'):
        src, dst = PRIOR / 'source' / name, ROOT / 'source' / name
        shutil.copy2(src, dst)
        assert src.read_bytes() == dst.read_bytes()
        adapters[name] = record(dst.read_bytes())
    receipt = dict(
        status='LOCAL_PACKAGED_NO_PHYSICAL_GO',
        inputs={str(STOCK.relative_to(WORK)): record(stock), str((REPORTER / 'artifacts/candidate.img').relative_to(WORK)): record(reporter)},
        candidate=record(image), full_p10=record(full), wrapped_ramdisk=record(ram), compressed_ramdisk_payload=record(payload), init=record(init), elf=elf,
        stock_raw_Image=record(raw), stock_gzip_stream=record(stream),
        stock_wrapped_kernel_before=record(kernel), wrapped_kernel_after=record(ak),
        stock_fdt_before=record(dt), fdt_after=record(newdt),
        preservation=dict(raw_Image_exact=True, gzip_stream_exact=True, kernel_wrapper_exact=True,
            reporter_wrapped_ramdisk_exact=True, reporter_recompressed=False, reporter_init_exact=True,
            header_addresses_page_bootargs_exact=True, dt_hardware_context_and_all_other_tokens_exact=True),
        deltas=dict(android_ramdisk_size_before=len(oldram), android_ramdisk_size_after=len(ram),
            android_id_before=header[576:608].hex(), android_id_after=ah[576:608].hex(),
            header_changed_byte_offsets=header_changes,
            dt_only_property='/chosen/bootargs', dt_token_before=old_token.decode(), dt_token_after=new_token.decode(),
            dt_changed_byte_offsets=changed_offsets(dt, newdt),
            kernel_changed_byte_offsets=changed_offsets(kernel, ak),
            dt_and_kernel_lengths_unchanged=True, alignment_padding='zero; regenerated for exact replacement size'),
        initrd=dict(wrapper_address='0x44000000', payload_start='0x44000200', payload_bytes=len(payload),
            payload_end_exclusive=f'0x{0x44000200 + len(payload):08x}', wrapper_excluded_bytes=512,
            linux_initrd_start_end_properties_added=False),
        installer=dict(literal_replacements=len(edits), source=record(installer.encode()),
            execute_Transport_Guard_byte_identical=True, adapters=adapters,
            parent_supplied_current_p10_preimage=CURRENT, fresh_device_observation=False,
            original_stock_admission_retained_via_inherited_preimages=True),
        copied_format_helpers=copies,
        identity=dict(run_id='9342cbf1-3bf0-44d4-b655-a1ca30146a99', usb_serial='P499342cbf13bf044d4b655',
            vid_pid='0b05:4a49', product='ASUS-PID1:<actual uname.release>', fat_label='P49RAM', report='PROBE.TXT'),
        nominal_reboot_attempt_seconds=60, physical_fallback_qualified=False,
        config_flags_available=False, config_flags_invented=False,
        scope=dict(network=False, device=False, private_data=False, ssh=False, root=False, install=False,
            reboot=False, kernel_build=False, c_compile=False, physical_execution_proven=False, fullOS_GO=False),
    )
    (ROOT / 'evidence/packaging-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({k: receipt[k] for k in ('status', 'candidate', 'full_p10', 'initrd')}, indent=2))


if __name__ == '__main__':
    main()
