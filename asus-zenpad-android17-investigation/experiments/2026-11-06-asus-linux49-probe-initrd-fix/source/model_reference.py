#!/usr/bin/env python3
"""Bounded offline semantic model of manually validated LK instructions.

NOT an ARM emulator. Storage/copy/string/FDT APIs are modeled by their observed
contracts; host zlib stands in for LK's inflate engine. No platform calls,
allocator, cache/MMU operation, secure monitor, or Linux kernel is executed.
Writes only small JSON evidence beneath this spike; input images remain frozen.
"""
from pathlib import Path
import hashlib
import json
import struct as S
import zlib

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT.parent
OUT = ROOT / 'evidence'
receipts = {}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(name, expected=None):
    data = (WORK / name).read_bytes()
    digest = sha(data)
    if expected is not None:
        assert digest == expected, (name, digest)
    receipts[name] = {'bytes': len(data), 'sha256': digest}
    return data


def align(n, a):
    return (n + a - 1) // a * a


LK = read('2026-11-05-asus-boot-access-audit/sources/firmware/lk.bin', 'c5b5017ee3efdf018d9b6be7db978f29365c30e60a3fb9173660fda699f7b765')
for saved in ('initial', 'verify'):
    saved_lk = read(f'2026-11-05-asus-boot-access-audit/artifacts/device-backup/{saved}/lk.bin')
    assert saved_lk[:len(LK)] == LK and not any(saved_lk[len(LK):])


def lkbytes(addr, count):
    off = addr - 0x41e00000 + 512
    return LK[off:off + count]


def word(addr):
    return S.unpack('<I', lkbytes(addr, 4))[0]


def lkstr(addr):
    return lkbytes(addr, 2048).split(b'\0')[0].decode()


# Reviewable anchors: fail if key instructions change, independent of comments.
anchors = {
    0x41e049f6: 'a5f50075',  # kernel wrapper destination minus 512
    0x41e04a76: '03f50073',  # recognized recovery source plus 512
    0x41e1dea4: '5869',      # destination = header.ramdisk_addr
    0x41e1deac: '07f086ed',  # memcpy
    0x41e1dedc: '6421',      # snprintf limit = 100
    0x41e1df54: '8de83000',  # stacked initrd destination and payload size
    0x41e1cf5e: 'c1f31205',  # low 19 bits of kernel address
    0x41e1cf96: '0335',      # round DT tail length upward
    0x41e1cf9a: '25f00305',
    0x41e1cfdc: '4ff0e073',  # inflate output capacity 28 MiB
    0x41e1d136: '09f077fd',  # set initrd-start
    0x41e1d176: '09f057fd',  # set initrd-end
    0x41e1d664: '09f0e0fa',  # replace bootargs
    0x41e1b880: '700060e1',  # ARM SMC #0
}
for a, expected in anchors.items():
    assert lkbytes(a, len(bytes.fromhex(expected))).hex() == expected
assert lkstr(0x41e4b974) == '%s'
assert word(0x41e1b8f4) == 0x82000200


def wrapper(data, expected):
    """0x4218 + 0x25d08 + 0x252a0: ASCII case-insensitive name, max32."""
    if len(data) < 40 or S.unpack_from('<I', data)[0] != 0x58881688:
        return -1
    name = data[8:40].split(b'\0')[0]
    if name.lower() != expected.lower():
        return -1
    return S.unpack_from('<I', data, 4)[0]


def scan_dt(memory, kernel_size):
    """0x1cf66–0x1cfa6: no compatible/board selection; last magic wins.

    Address zero relative to scratch is never checked after the decrement hits
    the lower bound. Tail length includes Android size's retained wrapper512.
    """
    assert kernel_size + 4 <= len(memory)
    for off in range(kernel_size, 0, -1):
        if memory[off:off + 4] == b'\xd0\x0d\xfe\xed':
            copied = align(kernel_size - off, 4)
            return off, copied, kernel_size - copied
    return None


def gzip_header_size(data):
    # 0x1e428 checks method and reserved flags, skips optional header fields.
    if len(data) < 10 or data[2] != 8 or data[3] & 0xe0:
        raise ValueError('LK gzip header rejection')
    flags = data[3]
    n = 10
    if flags & 4:
        n = 12 + S.unpack_from('<H', data, 10)[0]
    for mask in (8, 16):
        if flags & mask:
            n = data.index(b'\0', n) + 1
    if flags & 2:
        n += 2
    if n >= len(data):
        raise ValueError('LK gzip header >= supplied input size')
    return n


def lk_inflate_model(data, capacity=0x1c00000):
    n = gzip_header_size(data)
    obj = zlib.decompressobj(-15)  # LK 0x1e396 passes -15; no gzip trailer check
    raw = obj.decompress(data[n:], capacity)
    return {'success': obj.eof, 'output_bytes': len(raw),
            'output_sha256': sha(raw), 'capacity': capacity,
            'header_bytes': n, 'raw_deflate_input_bytes': len(data) - n,
            'unused_input_bytes': len(obj.unused_data)}, raw


def parse_dt(data):
    magic, total, so, st, mo, version, last, cpu, strs, structs = S.unpack_from('>10I', data)
    assert magic == 0xd00dfeed and total <= len(data)
    assert version == 17 and so + structs <= total and st + strs <= total
    strings = data[st:st + strs]
    props, stack = {}, []
    p = so
    while p < so + structs:
        token = S.unpack_from('>I', data, p)[0]
        p += 4
        if token == 1:
            end = data.index(b'\0', p)
            stack.append(data[p:end].decode())
            p = align(end + 1, 4)
        elif token == 2:
            stack.pop()
        elif token == 3:
            n, off = S.unpack_from('>II', data, p)
            p += 8
            key = strings[off:strings.index(b'\0', off)].decode()
            props[('/'.join(stack) or '/', key)] = data[p:p + n]
            p = align(p + n, 4)
        elif token == 9:
            break
        else:
            assert token == 4
    chosen = {}
    for name in ('bootargs', 'linux,initrd-start', 'linux,initrd-end'):
        value = props.get(('/chosen', name))
        if value is not None:
            chosen[name] = value.rstrip(b'\0').decode() if name == 'bootargs' else hex(int.from_bytes(value, 'big'))
    return {'total_size': total, 'sha256': sha(data[:total]), 'chosen': chosen}


def initrd_tokens(cmd):
    found = []
    for token in cmd.split():
        if token.startswith('initrd='):
            a, n = token[7:].split(',')
            start, size = int(a, 0), int(n, 0)
            found.append({'token': token, 'start': hex(start), 'size': size, 'end': hex(start + size)})
    return found


def inspect(name, expected):
    data = read(name, expected)
    assert data[:8] == b'ANDROID!'
    ks, ka, rs, ra, ss, sa, tags, page, ver, osv = S.unpack_from('<10I', data, 8)
    assert page == 2048 and ss == ver == 0
    ro = page + align(ks, page)
    k, r = data[page:page + ks], data[ro:ro + rs]
    ksize, rsize = wrapper(k, b'KERNEL'), wrapper(r, b'recovery')
    assert (ksize, rsize) == (ks - 512, rs - 512)
    cmd = data[64:576].split(b'\0')[0].decode()
    copied_cmd = cmd[:99]  # snprintf(..., 100, "%s", header.cmdline)
    padded_hash = hashlib.sha256(data)
    remaining = 0xff7000 - len(data)
    assert remaining >= 0
    while remaining:
        count = min(remaining, 1024 * 1024)
        padded_hash.update(bytes(count))
        remaining -= count
    # Header loader rootfs = scratch + align(ks); payload loader subtracts
    # kernel wrapper512, then adds recognized ramdisk wrapper512.
    scratch = 0x45000000
    rootfs_wrapper = scratch + align(ks, page) - 512
    rootfs_payload = rootfs_wrapper + 512
    loaded = data[page + 512:]
    selected = scan_dt(loaded, ks)
    assert selected is not None
    off, copied, gzip_limit = selected
    dt = parse_dt(loaded[off:off + copied])
    gz = zlib.decompressobj(31)
    full_raw = gz.decompress(k[512:], 32 * 1024**2)
    assert gz.eof and not gz.unconsumed_tail
    true_gzip_size = len(k[512:]) - len(gz.unused_data)
    modeled, raw = lk_inflate_model(loaded[:gzip_limit])
    assert modeled['success'] and raw == full_raw
    text_offset, image_size = S.unpack_from('<QQ', raw, 8)
    config_start = raw.find(b'IKCFG_ST')
    embedded_config = None
    if config_start >= 0:
        config_bytes = zlib.decompress(raw[config_start + 8:], 31)
        embedded_config = {'marker_offset': config_start, 'full_config_sha256': sha(config_bytes), 'selected_lines': [line for line in config_bytes.decode().splitlines() if 'CONFIG_CMDLINE' in line or 'CONFIG_BLK_DEV_INITRD' in line]}
    moved = r[512:512 + rsize]
    assert len(moved) == rsize and moved[:2] == b'\x1f\x8b'
    header_tokens = initrd_tokens(copied_cmd)
    final_pair = (ra, ra + rsize)
    effective_pair = final_pair
    if header_tokens:
        last = header_tokens[-1]
        effective_pair = int(last['start'], 16), int(last['end'], 16)
    offset = effective_pair[0] - ra
    prefix = moved[offset:offset + 16] if 0 <= offset < len(moved) else b''
    result = {
        'image_sha256': sha(data), 'image_bytes': len(data), 'zero_padded_p10_sha256': padded_hash.hexdigest(),
        'header': {'kernel_size': ks, 'kernel_addr': hex(ka), 'ramdisk_size': rs, 'ramdisk_addr': hex(ra), 'tags_addr': hex(tags), 'page_size': page, 'os_version': hex(osv)},
        'wrappers': {'kernel_recognized': True, 'recovery_recognized_case_insensitive': True, 'kernel_payload_size': ksize, 'ramdisk_payload_size': rsize, 'wrapped_kernel_sha256': sha(k), 'compressed_ramdisk_sha256': sha(moved)},
        'load': {'kernel_wrapper_destination': hex(scratch - 512), 'kernel_gzip_source': hex(scratch), 'ramdisk_wrapper_source': hex(rootfs_wrapper), 'ramdisk_payload_source': hex(rootfs_payload), 'ramdisk_copy_destination': hex(ra), 'ramdisk_copy_bytes': rsize},
        'dt_selection': {'algorithm': 'last backward magic, no compatible match', 'source_offset_from_gzip': off, 'source_address': hex(scratch + off), 'copied_tail_bytes': copied, 'destination': hex(tags), 'android_kernel_size_retains_wrapper': True, 'parsed': dt},
        'decompression': {**modeled, 'true_gzip_stream_bytes': true_gzip_size, 'LK_supplied_input_bytes': gzip_limit, 'gzip_trailer_bytes_omitted': true_gzip_size - gzip_limit, 'destination': hex(ka), 'text_offset': hex(text_offset), 'image_size': image_size, 'reserved_end_from_Image': hex(ka + image_size), 'file_end': hex(ka + len(raw)), 'address_low_19_bits_zero': (ka & 0x7ffff) == 0},
        'embedded_kernel_config': embedded_config,
        'cmdline': {'header': cmd, 'header_bytes': len(cmd), 'copied_header': copied_cmd, 'header_truncated': copied_cmd != cmd, 'LK_initial_default': lkstr(0x41e5b964), 'DT_original_bootargs_replaced_not_merged': True, 'header_initrd_tokens_retained': header_tokens, 'full_runtime_string_modeled': False},
        'modeled_FDT_writes': {'linux,initrd-start': hex(ra), 'linux,initrd-start_bytes': S.pack('>I', ra).hex(), 'linux,initrd-end': hex(ra + rsize), 'linux,initrd-end_bytes': S.pack('>I', ra + rsize).hex(), 'property_bytes_each': 4},
        'effective_initrd_with_no_extra_runtime_initrd_token': {'start': hex(effective_pair[0]), 'end': hex(effective_pair[1]), 'offset_into_moved_stream': offset, 'first_16_bytes_hex': prefix.hex(), 'gzip_magic_at_effective_start': prefix[:2] == b'\x1f\x8b', 'agrees_with_moved_payload': effective_pair == final_pair},
        'SMC_arguments_if_reached': {'r0': '0x82000200', 'r1': hex(ka), 'r2': hex(tags), 'r3': '0x0', 'r4': '0x1', 'post_SMC_PC_x0_x1_x2_x3': 'not proven by LK; secure monitor boundary'},
    }
    return result, loaded, moved


probe, loaded, moved = inspect('2026-11-06-asus-android17-build-continuation/artifacts/probe-r2/UNTESTED-combined-linux49-ram-probe.img', '48bb6efa1620cb380037e53b53cfa560e38cd23b95211c8634616ce94fd6ce48')
rescue, _, _ = inspect('2026-11-06-asus-android17-target-rescue/artifacts/candidate-delivery/UNTESTED-target-rescue.img', '93d647ea58784aefe4104cb0cbddbac04fe6169b30923ad63c5684e0dc920419')
assert rescue['wrappers']['wrapped_kernel_sha256'] == 'b0e5d48bf2889b418dda0fc867f70e42e27a0aeb0a0a3d37539d9a7435430880'
assert probe['zero_padded_p10_sha256'] == '25812e7dde39ec37e3f4c9438341cc29f2b2e7dce61e4b88d0886cd9dd075b16'
stock = read('2026-11-05-asus-boot-access-audit/artifacts/device-backup/initial/recovery.bin', '902b2f06a01cca574b4aa374e67c4e7f8f0ed53f6e6a55017b6d96351f0f1f20')
stock_ks = S.unpack_from('<I', stock, 8)[0]
stock_page = S.unpack_from('<I', stock, 36)[0]
assert sha(stock[stock_page:stock_page + stock_ks]) == rescue['wrappers']['wrapped_kernel_sha256']
compiled = read('2026-11-06-asus-android17-build-continuation/artifacts/Image.gz-dtb-combined-r1', 'd4094bcff6c763af7f1c01ccd3d612a988f96de13f78b492b808cc76c0ac929f')
gz = zlib.decompressobj(31)
gz.decompress(compiled)
compiled_gzip = compiled[:len(compiled) - len(gz.unused_data)]
probe_gzip = loaded[:probe['decompression']['true_gzip_stream_bytes']]
assert compiled_gzip == probe_gzip
assert sha(probe_gzip) == 'acd66b0e487c9b3cf6170b471847e5b6b83478ca50a00ce6c7cbcae8401951e5'

tests = []


def check(name, condition, evidence):
    assert condition, name
    tests.append({'name': name, 'pass': True, 'evidence': evidence})


test_wrapper = S.pack('<II', 0x58881688, 123) + b'RECOVERY\0' + bytes(23)
check('uppercase_RECOVERY_matches_lowercase_recovery', wrapper(test_wrapper, b'recovery') == 123, 'ASCII lowercase helper is at 0x41e252a0')
check('ROOTFS_does_not_match_recovery', wrapper(test_wrapper, b'ROOTFS') == -1, 'Different-name branch returns -1; full Android ramdisk size would then be used')
check('missing_magic_rejected_by_wrapper_parser', wrapper(bytes(40), b'recovery') == -1, 'No unconditional +512 assumption')
check('kernel_alignment_boundary', ((0x40080000 & 0x7ffff) == 0 and (0x40080001 & 0x7ffff) != 0), 'Unaligned kernel reaches permanent loop 0x41e1d01c')
check('no_DT_magic_has_no_selection', scan_dt(bytes(68), 64) is None, 'LK missing-DT path does not prove a usable fallback')
synthetic = bytearray(68)
synthetic[12:16] = synthetic[40:44] = b'\xd0\x0d\xfe\xed'
check('later_magic_wins_even_without_valid_tree', scan_dt(synthetic, 64)[0] == 40, 'Separate FDT header/open checks must validate selection')
bad = bytearray(probe_gzip)
bad[2] = 7
try:
    lk_inflate_model(bad)
    bad_rejected = False
except ValueError:
    bad_rejected = True
check('wrong_gzip_method_rejected', bad_rejected, '0x41e1e430/0x41e1e432')
limited, _ = lk_inflate_model(probe_gzip, 1024)
check('small_inflate_output_capacity_cannot_finish', not limited['success'], limited)
check('probe_stale_token_disagrees_with_relocation', not probe['effective_initrd_with_no_extra_runtime_initrd_token']['agrees_with_moved_payload'], probe['effective_initrd_with_no_extra_runtime_initrd_token'])
check('wrong_start_is_not_gzip_or_newc', moved[512:514] != b'\x1f\x8b' and moved[512:518] not in (b'070701', b'070702'), moved[512:528].hex())
corrected = probe['cmdline']['header'].replace('initrd=0x44000200,0x11f7b0', 'initrd=0x44000000,0x11f7b0')
check('corrected_header_token_matches_LK', initrd_tokens(corrected)[0]['start'] == probe['modeled_FDT_writes']['linux,initrd-start'] and initrd_tokens(corrected)[0]['end'] == probe['modeled_FDT_writes']['linux,initrd-end'], corrected)
removed = probe['cmdline']['header'].replace(' initrd=0x44000200,0x11f7b0', '')
check('removing_header_token_leaves_DT_authoritative', not initrd_tokens(removed), removed)
check('rescue_DT_old_2MiB_token_not_in_header', '0x200000' in rescue['dt_selection']['parsed']['chosen']['bootargs'] and not rescue['cmdline']['header_initrd_tokens_retained'], rescue['cmdline']['header'])
boundary = [{'payload_size': n, 'LK_start': '0x44000000', 'LK_end': hex(0x44000000 + n), 'old_DT_2MiB_value_used': False} for n in (0x1fffff, 0x200000, 0x200001, 0x240000)]
check('ramdisk_size_crosses_2MiB_without_clamp_in_traced_path', boundary[2]['LK_end'] == '0x44200001', boundary)

source_excerpts = []
for name, bounds in {
    'arch/arm64/mm/init.c': [(64, 81)],
    'arch/arm64/kernel/setup.c': [(180, 201), (241, 260)],
    'drivers/of/fdt.c': [(903, 925), (1090, 1135), (1248, 1275)],
}.items():
    full = '2026-11-06-asus-linux49-probe-review/source/kernel/' + name
    data = read(full)
    lines = data.decode().splitlines()
    for first, last in bounds:
        source_excerpts.append(full + f' lines {first}-{last}\n' + '\n'.join(f'{n}: {lines[n-1]}' for n in range(first, min(last, len(lines)) + 1)))
for name in [
    '2026-11-06-asus-linux49-probe-review/evidence/source-pins.json',
    '2026-11-06-asus-linux49-probe-review/evidence/artifact-inspection.json',
    '2026-11-06-asus-linux49-probe-review/evidence/packaged-dt-properties.json',
    '2026-11-06-asus-linux49-probe-review/evidence/reserved-memory-check.json',
    '2026-11-06-asus-android17-build-continuation/evidence/combined-r1.config',
    '2026-11-05-asus-boot-access-audit/evidence/live-lk-official-comparison.json',
    '2026-11-06-asus-custom-boot-path/evidence/lk-acceptance-review.md',
    '2026-11-06-asus-android17-orchestration/evidence/stock-control-runtime-20261106.json',
    '2026-11-06-asus-android17-orchestration/evidence/explicit-recovery-inverse-runtime-20261106.json',
]:
    read(name)
pins = json.loads((WORK / '2026-11-06-asus-linux49-probe-review/evidence/source-pins.json').read_text())
for name in ('arch/arm64/mm/init.c', 'arch/arm64/kernel/setup.c', 'drivers/of/fdt.c'):
    actual = receipts['2026-11-06-asus-linux49-probe-review/source/kernel/' + name]['sha256']
    assert pins[name]['sha256'] == actual and pins[name]['matches_receipt']
config = (WORK / '2026-11-06-asus-android17-build-continuation/evidence/combined-r1.config').read_text()
source_excerpts.append('\n'.join(line for line in config.splitlines() if 'CONFIG_CMDLINE' in line or 'CONFIG_BLK_DEV_INITRD' in line))

output = {
    'kind': 'STATIC_SEMANTIC_MODEL_NOT_CPU_EMULATION_NOT_PHYSICAL_BOOT_PROOF',
    'contracts': ['Recovery dispatch boot mode 2; preloader kernel_boot_opt selects 64-bit path.', 'Storage returns the exact image bytes; allocation and memcpy succeed.', 'FDT open/setprop/pack succeed and their documented byte-copy contracts apply.', 'Host zlib raw inflate stands in for LK zlib1.2.3; no LK inflate instructions executed.', 'Runtime strings and callbacks are not invented; no additional runtime initrd token is assumed for the conditional effective-range prediction.', 'SMC is a stop boundary; post-SMC execution and final AArch64 x0 are not emulated.'],
    'instruction_anchors': {hex(a): b for a, b in anchors.items()},
    'bitness_selector': {'preloader_field': '[*[GOT+0x148]+0x14c]', 'call': '0x41e02cf8 -> 0x41e02c74', '64_bit_values': [0, 1, 4, 5], '32_bit_values': [2, 3], 'out_of_range': '32-bit', 'runtime_value': 'not read in this offline audit', 'Android_header_bootopt_string_does_not_set_this_flag_in_traced_path': True},
    'common_handoff_optional_hook_GOT_slots': {hex(off): hex(word(0x41e6500c + off)) for off in (0xec, 0x188, 0x334, 0x3a0, 0x3bc, 0x160, 0x7c, 0x40, 0x2fc, 0x164, 0x1c8, 0x300, 0x298, 0x2f8, 0x2b0, 0x304, 0xd4, 0x2e4, 0x2b4, 0x290, 0x154, 0x378, 0x5c, 0x27c)},
    'probe': probe, 'stock_kernel_rescue_unarmed': rescue,
    'proposed_correction_not_applied': {'preferred_header_cmdline': removed, 'alternative_explicit_header_cmdline': corrected, 'DT_consistency_start': '0x44000000', 'DT_consistency_end': probe['modeled_FDT_writes']['linux,initrd-end'], 'keep_Android_ramdisk_addr': '0x44000000', 'keep_compressed_payload_and_wrappers_unchanged': True},
    'boundary_tests': tests,
}
(OUT / 'handoff-model.json').write_text(json.dumps(output, indent=2) + '\n')
(OUT / 'source-excerpts.txt').write_text('\n\n'.join(source_excerpts) + '\n')
(OUT / 'input-receipts.json').write_text(json.dumps(receipts, indent=2) + '\n')
print(json.dumps({'probe': probe['effective_initrd_with_no_extra_runtime_initrd_token'], 'rescue': rescue['effective_initrd_with_no_extra_runtime_initrd_token'], 'boundary_tests_passed': len(tests)}, indent=2))
