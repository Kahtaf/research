"""One local source/ELF/package preservation check and stock-only packaging."""
from pathlib import Path
import ast
import difflib
import gzip
import hashlib
import json
import re
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT.parent
CONTROL = WORK / '2026-11-07-asus-stock-exact-usb-reporter-control'
REPORTER = WORK / '2026-11-07-asus-linux49-usb-ram-report'
STOCK = WORK / '2026-11-07-asus-stock-kernel-version-control/artifacts/original.img'
CURRENT = '039c5a52d9ac04fd515c2081c455066057d1503d6979fc81a5b2c70712bc7dba'
MARKER = 'ASUS-RAM-FAILLOG-20261107-R1'


def boundary(event, args):
    if event == 'open':
        path = str(args[0])
        assert not any(s in path for s in ('/private/', '/device-backup/', 'root_shell_wifi.py', 'mtk-su-mirror-b', '/dev/')), path
    if event.startswith(('subprocess.', 'socket.')) or event in ('os.system', 'os.posix_spawn'):
        raise RuntimeError('Packaging cannot launch processes or use network: ' + event)


sys.addaudithook(boundary)
sys.path.insert(0, str(ROOT / 'source'))
import bootformat as b
import fdt

sha = lambda data: hashlib.sha256(data).hexdigest()
record = lambda data: dict(bytes=len(data), sha256=sha(data))


def block(source, name):
    node = next(n for n in ast.parse(source).body if getattr(n, 'name', None) == name)
    return ''.join(source.splitlines(True)[node.lineno - 1:node.end_lineno])


def changed_offsets(before, after):
    assert len(before) == len(after)
    return [i for i, (a, b) in enumerate(zip(before, after)) if a != b]


def closing(source, start, opening, ending):
    depth, quoted, escaped = 0, False, False
    for pos in range(start, len(source)):
        c = source[pos]
        if quoted:
            if escaped: escaped = False
            elif c == '\\': escaped = True
            elif c == '"': quoted = False
        elif c == '"': quoted = True
        elif c == opening: depth += 1
        elif c == ending:
            depth -= 1
            if not depth: return pos
    raise AssertionError('Unclosed C expression')


def cbody(source, name):
    start = re.search(r'\b' + name + r'\([^)]*\)\s*\{', source).end() - 1
    return source[start:closing(source, start, '{', '}') + 1]


def setup_operations(source):
    body = cbody(source, 'setup')
    operations = {'getpid', 'mount', 'make_fat', 'ram_report', 'unique_udc', 'mkdir', 'equals', 'put', 'symlink'}
    found = []
    for m in re.finditer(r'"(?:\\.|[^"\\])*"|/\*[\s\S]*?\*/|(?P<call>\b[A-Za-z_]\w*)\s*\(', body):
        name = m.group('call')
        if name not in operations: continue
        start = m.end() - 1
        args = body[start + 1:closing(body, start, '(', ')')]
        found.append((name, re.sub(r'\s+', '', args)))
    return found


def main():
    assert not (ROOT / 'evidence/packaging-receipt.json').exists(), 'One essential package check only'
    source = (ROOT / 'source/init.c').read_text()
    original_c = (REPORTER / 'source/init.c').read_text()
    assert setup_operations(source) == setup_operations(original_c)
    fat_original = cbody(original_c, 'make_fat').split('memset(fat,', 1)[1]
    assert cbody(source, 'make_fat').split('memset(fat,', 1)[1] == fat_original
    for macro in ('RUN_ID', 'USB_SERIAL', 'G', 'LUN', 'RAMFILE', 'FAT_BYTES', 'TMPFS_MAGIC'):
        assert re.search(r'^#define ' + macro + r' .+$', source, re.M)[0] == re.search(r'^#define ' + macro + r' .+$', original_c, re.M)[0]
    for guard in ('!S_ISREG(st.st_mode)', 'st.st_nlink!=1', 'st.st_size!=0', 'fs.f_type!=TMPFS_MAGIC', 'st.st_size!=FAT_BYTES', '(st.st_mode&0777)!=0444'):
        assert guard in cbody(source, 'ram_report') and guard in cbody(original_c, 'ram_report')
    for policy in ('attempt<100', 'count>1', 'errno!=ENOENT', 'struct timespec t={0,100000000}', 'clock_nanosleep(CLOCK_MONOTONIC,0,&t,NULL)'):
        assert policy in cbody(source, 'unique_udc') and policy in cbody(original_c, 'unique_udc')
    for policy in ('alarm(60)', 'end.tv_sec+=60', 'CLOCK_MONOTONIC,TIMER_ABSTIME,&end,NULL', 'while(r==EINTR)', 'for(;;)pause()'):
        assert policy in source and policy in original_c
    assert source.index('log_open();log_uname();') < source.index('int setup_rc=setup();')
    assert 'O_WRONLY|O_CLOEXEC|O_NOFOLLOW|O_NONBLOCK' in cbody(source, 'log_open')
    assert 'makedev(1,11)' in source and 'unlink(LOG_NODE)' in source
    assert not any(s in source for s in ('mmcblk', 'system(', 'execve(', 'socket(', 'nodename', 'domainname'))
    assert len(setup_operations(source)) == 40

    copies = {}
    for name in ('bootformat.py', 'fdt.py', 'adb', 'legacy_adb.py'):
        data = (ROOT / 'source' / name).read_bytes()
        assert data == (CONTROL / 'source' / name).read_bytes()
        copies[name] = record(data)
    init = (ROOT / 'artifacts/init').read_bytes()
    build = json.loads((ROOT / 'evidence/build-log.json').read_text())
    attempt = json.loads((ROOT / 'evidence/compile-2-attempt.json').read_text())
    assert build['returncode'] == 0 and build['compilations'] == 1 and build['parallelism'] == 1
    assert sha(init) == build['init_sha256'] and sha(source.encode()) == attempt['source_sha256']
    elf = b.elf_static(init)
    for marker in (MARKER, '9342cbf1-3bf0-44d4-b655-a1ca30146a99', 'P499342cbf13bf044d4b655', 'ASUS-PID1:%s', 'P49RAM', 'PROBE   TXT', 'put.write', 'equals.mismatch', 'setup.return.-1', 'udc.bind'):
        assert marker.encode() in init, marker

    stock = STOCK.read_bytes()
    control = (CONTROL / 'artifacts/candidate.img').read_bytes()
    assert len(stock) == 7804928 and sha(stock) == 'f0bf4834a2d3ec207590c6742d0adb4fd9a3adc9a2dab5d0ec7c28f27963b140'
    assert sha(control) == 'e7d5f3c93a1c94d0f27c3f19e7b29aab32d70d5139e296bad8ab749c3852c57e'
    header, kernel, oldram, tail = b.parse_image(stock)
    ch, ck, cr, cx = b.parse_image(control)
    assert not tail and not cx
    assert sha(kernel) == 'd585f856946b4f4e02f95e7ef796423a046ce7c0c2a661680abd87b8b5326952'
    raw, dt = b.ungzip(kernel[512:])
    stream = kernel[512:-len(dt)]
    assert sha(raw) == 'db90ee7fff379f35ac2b0aafb11a6abee7b2c283b57d352c40ae7c6d7c35eb2a'
    assert sha(dt) == '77e2d8fbeced5a827ede6c0b8589140e9211d8dc3ca77aaa31a1dd1787a9c455'
    entries = {n: (0o40755, 0, 0, b'') for n in ('dev', 'proc', 'sys', 'config', 'ram')}
    entries['init'] = (0o100755, 0, 0, init)
    cp = b.make_cpio(entries)
    assert b.parse_cpio(cp) == entries
    gz = bytearray(gzip.compress(cp, compresslevel=9, mtime=0)); gz[9] = 255
    payload = bytes(gz)
    ram = b.wrap(cr, payload)
    assert ram[:4] == cr[:4] and ram[8:512] == cr[8:512]
    _, nodes, tokens = fdt.parse(dt)
    old_token = b'initrd=0x44000200,0x200000'
    new_token = f'initrd=0x44000200,0x{len(payload):06x}'.encode()
    assert len(old_token) == len(new_token) and dt.count(old_token) == 1
    assert nodes['/chosen']['bootargs'].split().count(old_token + b'\0') == 1
    newdt = dt.replace(old_token, new_token)
    _, newnodes, newtokens = fdt.parse(newdt)
    expected = {n: dict(p) for n, p in nodes.items()}
    expected['/chosen']['bootargs'] = nodes['/chosen']['bootargs'].replace(old_token, new_token)
    assert newnodes == expected and len(tokens) == len(newtokens)
    for before, after in zip(tokens, newtokens):
        if before != after:
            assert before[:3] == after[:3] == (3, '/chosen', 'bootargs')
            assert before[4].replace(old_token, new_token) == after[4]
    newkernel = b.wrap(kernel, stream + newdt)
    assert newkernel[:512] == kernel[:512] and len(newkernel) == len(kernel)
    image = b.make_image(header, newkernel, ram)
    full = image + bytes(b.PARTITION_SIZE - len(image))
    (ROOT / 'artifacts/candidate.img').write_bytes(image)
    (ROOT / 'artifacts/candidate.p10.raw').write_bytes(full)
    (ROOT / 'artifacts/ramdisk.wrapped').write_bytes(ram)
    ah, ak, ar, ax = b.parse_image((ROOT / 'artifacts/candidate.img').read_bytes())
    araw, adt = b.ungzip(ak[512:]); acp, extra = b.ungzip(ar[512:])
    assert not ax and not extra and ar == ram and b.parse_cpio(acp) == entries
    assert araw == raw and adt == newdt and ak[512:-len(adt)] == stream
    assert (ROOT / 'artifacts/candidate.p10.raw').read_bytes() == full
    header_changes = changed_offsets(header, ah)
    assert set(header_changes) <= set(range(16, 20)) | set(range(576, 608))
    assert ah[64:576] == header[64:576] == ch[64:576]
    assert b'console=null' not in ah[64:576] and b'maxcpus=' not in ah[64:576]
    assert ah == b.make_image(header, newkernel, ram)[:2048]

    original = (CONTROL / 'source/install.py').read_text()
    edits = {
        "IMAGE_SHA='e7d5f3c93a1c94d0f27c3f19e7b29aab32d70d5139e296bad8ab749c3852c57e'": f"IMAGE_SHA='{sha(image)}'",
        f"FULL_SHA='{CURRENT}'": f"FULL_SHA='{sha(full)}'",
        'len(image)==7737344': f'len(image)=={len(image)}',
        "profile='exact-stock-3.18.35-unchanged-ram-usb-pid1-reporter-control'": "profile='exact-stock-3.18.35-ram-usb-pid1-reporter-failure-log-r1'",
    }
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
    (ROOT / 'source/install.diff').write_text(''.join(difflib.unified_diff(original.splitlines(True), installer.splitlines(True), fromfile='stockcontrol/source/install.py', tofile='source/install.py')))
    expected_installer = installer
    for old, new in reversed(list(edits.items())):
        assert expected_installer.count(new) == 1
        expected_installer = expected_installer.replace(new, old)
    assert expected_installer == original

    receipt = dict(
        status='LOCAL_PACKAGED_NO_PHYSICAL_OR_FULLOS_GO',
        candidate=record(image), full_p10=record(full), init=record(init), source=record(source.encode()), elf=elf,
        wrapped_ramdisk=record(ram), compressed_ramdisk_payload=record(payload),
        inputs={str(STOCK.relative_to(WORK)): record(stock), str((CONTROL / 'artifacts/candidate.img').relative_to(WORK)): record(control), str((REPORTER / 'source/init.c').relative_to(WORK)): record(original_c.encode())},
        stock_raw_Image=record(raw), stock_gzip_stream=record(stream), stock_wrapped_kernel_before=record(kernel), wrapped_kernel_after=record(ak), stock_fdt_before=record(dt), fdt_after=record(newdt),
        preservation=dict(raw_Image_exact=True, gzip_stream_exact=True, kernel_wrapper_exact=True, header_addresses_page_bootargs_exact=True, dt_hardware_and_all_other_properties_exact=True, setup_operation_arguments_and_order_exact=True, setup_operation_count=len(setup_operations(source)), fat_generation_and_report_bytes_exact_for_same_uname=True, ram_lun_guards_retained=True, original_udc_absence_policy_retained=True, nominal_60_second_deadline_retained=True),
        deltas=dict(android_ramdisk_size_before=len(oldram), android_ramdisk_size_control=len(cr), android_ramdisk_size_after=len(ram), android_id_before=header[576:608].hex(), android_id_after=ah[576:608].hex(), header_changed_byte_offsets=header_changes, dt_only_property='/chosen/bootargs', dt_token_before=old_token.decode(), dt_token_control='initrd=0x44000200,0x03e4a3', dt_token_after=new_token.decode(), dt_changed_byte_offsets=changed_offsets(dt, newdt), kernel_changed_byte_offsets=changed_offsets(kernel, ak), kernel_changed_byte_offsets_vs_control=changed_offsets(ck, ak), dt_and_kernel_lengths_unchanged=True, ram_wrapper_changes='payload length at bytes 4..7 only; gzip/cpio/init replaced', alignment_padding='zero; regenerated for replacement size'),
        initrd=dict(wrapper_address='0x44000000', payload_start='0x44000200', payload_bytes=len(payload), payload_end_exclusive=f'0x{0x44000200+len(payload):08x}', wrapper_excluded_bytes=512, linux_initrd_start_end_properties_added=False),
        logging=dict(revision=MARKER, sink='preopened initial RAM-root char 1:11, unlinked before setup mounts', normal_record_cap=64, normal_record_bytes_max=511, signal_records_max=2, signal_record_bytes_max=160, ram_fallback_bytes=8192, sink_open_flags='WRONLY|CLOEXEC|NOFOLLOW|NONBLOCK', errno_preserved_around_logging=True, private_values_logged=False, uname_fields=['sysname', 'release', 'version', 'machine'], sink_failure_limitation='Sink failures recorded in RAM only; unavailable kernel sink cannot survive reboot. No claim of retained-log readability until parent trial.'),
        installer=dict(literal_replacements=len(edits), source=record(installer.encode()), execute_Transport_Guard_byte_identical=True, only_candidate_pins_length_profile_preimage_changed=True, parent_supplied_current_p10_preimage=CURRENT, fresh_device_observation=False, copied_format_helpers_and_legacy_adapters=copies),
        build=dict(attempts=2, successful_compiles=1, second_compile_explicitly_authorized=True, first_failure='three ignored logging write return values under -Werror', parallelism=1, active_android_builds_touched=False),
        scope=dict(device=False, private_data=False, install=False, reboot=False, kernel_build=False, kernel_edits=False, broad_tests=False, physical_execution_proven=False, fullOS_GO=False),
        verification_limit='Static source/ELF/package preservation only. No runtime/helper execution, USB validation, or proof of printk/last_kmsg retention. Isolated PLAN documented separately.',
    )
    (ROOT / 'evidence/packaging-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({k: receipt[k] for k in ('status', 'candidate', 'full_p10', 'init', 'initrd')}, indent=2))


if __name__ == '__main__':
    main()
