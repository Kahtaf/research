"""Finite offline artifact inspection; no candidate generation or target execution."""
from pathlib import Path
import hashlib, json, re, resource, struct as S, zlib
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM

resource.setrlimit(resource.RLIMIT_CPU, (60, 60))
R = Path(__file__).resolve().parents[1]
W = R.parent
O = R / 'evidence'
pins = {}
sha = lambda b: hashlib.sha256(b).hexdigest()
align = lambda n, a: (n + a - 1) // a * a


def read(rel, pin=None, maxbytes=32*1024**2):
    p = W / rel
    assert p.stat().st_size <= maxbytes
    b = p.read_bytes()
    h = sha(b)
    assert pin is None or h == pin, (rel, h)
    pins[rel] = {'bytes': len(b), 'sha256': h}
    return b


def dt_parse(b):
    h = S.unpack_from('>10I', b)
    assert h[0] == 0xd00dfeed and 40 <= h[1] <= len(b)
    assert h[2]+h[9] <= h[1] and h[3]+h[8] <= h[1]
    strings = b[h[3]:h[3]+h[8]]
    p, stack, props = h[2], [], {}
    for _ in range(20000):
        t = S.unpack_from('>I', b, p)[0]; p += 4
        if t == 1:
            end = b.index(0, p); stack.append(b[p:end].decode()); p = align(end+1, 4)
        elif t == 2: stack.pop()
        elif t == 3:
            n, off = S.unpack_from('>II', b, p); p += 8
            key = strings[off:strings.index(0, off)].decode()
            props[('/'.join(stack) or '/', key)] = b[p:p+n]; p = align(p+n, 4)
        elif t == 9: break
        else: assert t == 4
        assert p <= h[2]+h[9]
    else: raise AssertionError('FDT token bound')
    res = []; p = h[4]
    for _ in range(128):
        a, n = S.unpack_from('>QQ', b, p); p += 16
        if a == n == 0: break
        res.append({'start': hex(a), 'bytes': n, 'end': hex(a+n)})
    selected = []
    for (path, key), val in props.items():
        if path == '/chosen' or path.startswith('/reserved-memory') or path.startswith('/memory'):
            selected.append({'path': path, 'name': key, 'hex': val.hex(),
                             'text': val.rstrip(b'\0').decode() if all(c == 0 or 32 <= c < 127 for c in val) else None})
    return {'sha256': sha(b[:h[1]]), 'header': list(h), 'properties': selected, 'reservations': res}, props


def gz(b):
    d = zlib.decompressobj(31)
    out = d.decompress(b, 32*1024**2)
    assert d.eof and not d.unconsumed_tail
    return out, len(b)-len(d.unused_data), d.unused_data


def cpio_end(b):
    p = 0
    for _ in range(4096):
        assert b[p:p+6] in (b'070701', b'070702')
        f = [int(b[p+6+i*8:p+14+i*8], 16) for i in range(13)]
        n = f[11]; assert 0 < n < 4096
        name = b[p+110:p+110+n-1].decode()
        p = align(p+110+n, 4); p = align(p+f[6], 4)
        assert p <= len(b)
        if name == 'TRAILER!!!': return p
    raise AssertionError('cpio entry bound')


sources = {
    'original_initial': ('2026-11-05-asus-boot-access-audit/artifacts/device-backup/initial/recovery.bin', '902b2f06a01cca574b4aa374e67c4e7f8f0ed53f6e6a55017b6d96351f0f1f20'),
    'original_verify': ('2026-11-05-asus-boot-access-audit/artifacts/device-backup/verify/recovery.bin', '902b2f06a01cca574b4aa374e67c4e7f8f0ed53f6e6a55017b6d96351f0f1f20'),
    'failed_rescue': ('2026-11-06-asus-stock-only-ram-rescue-build/artifacts/candidate/UNAPPROVED-STOCK-ONLY.img', '5a61d3d65a7ba6b29745a965d9911ab4483c951a0327339839a0541bcb9ab30f'),
    'minimal_pending': ('2026-11-06-asus-minimal-ram-usb-probe/artifacts/candidate.img', '535ad86471739967c0e68c058787cf2e5ac6bd844765b75d4bb576200a01d40e'),
}
images = {}; original_kernel = None
for label, (path, pin) in sources.items():
    b = read(path, pin); assert b[:8] == b'ANDROID!'
    fields = S.unpack_from('<10I', b, 8)
    ks, ka, rs, ra, ss, sa, tags, page, dts, unused = fields
    assert page == 2048 and ss == dts == 0 and unused == 234881318
    ro = page+align(ks, page); k = b[page:page+ks]; r = b[ro:ro+rs]
    for comp, name in ((k, b'kernel'), (r, b'recovery')):
        assert comp[:4] == bytes.fromhex('88168858')
        assert comp[8:40].split(b'\0')[0].lower() == name
        assert S.unpack_from('<I', comp, 4)[0] == len(comp)-512
    assert b[576:608] == hashlib.sha1(k+S.pack('<I', ks)+r+S.pack('<II', rs, 0)).digest()+bytes(12)
    assert sha(k) == 'b0e5d48bf2889b418dda0fc867f70e42e27a0aeb0a0a3d37539d9a7435430880'
    if original_kernel is None: original_kernel = k
    assert k == original_kernel
    payload = r[512:]; raw, used, rest = gz(payload)
    # Exact LK scans with wrapped Android kernel_size from its post-wrapper staging base.
    staged = b[page+512:]
    selected_dt = staged.rfind(bytes.fromhex('d00dfeed'), 1, ks+4)
    assert selected_dt == 7409347
    copied_tail = align(ks-selected_dt,4)
    selected_fdt, _ = dt_parse(staged[selected_dt:selected_dt+copied_tail])
    assert selected_fdt['sha256'] == '77e2d8fbeced5a827ede6c0b8589140e9211d8dc3ca77aaa31a1dd1787a9c455'
    # Exact first DEFLATE EOS consumption, excluding the 8-byte gzip trailer.
    assert payload[:4] == b'\x1f\x8b\x08\x00'
    rd = zlib.decompressobj(-15); rdout = rd.decompress(payload[10:], 32*1024**2)
    assert rd.eof and rdout == raw and not rd.unconsumed_tail
    eos = 10+len(payload[10:])-len(rd.unused_data)
    assert eos+8 == used
    partial_raw = zlib.decompressobj(-15)
    partial_raw.decompress(payload[10:0x200000], 32*1024**2)
    short = zlib.decompressobj(31); expanded = short.decompress(payload[:0x200000], 32*1024**2)
    raw_end = None; second_offset = None
    if any(rest):
        second_offset = used+len(rest)-len(rest.lstrip(b'\0'))
        raw_end = second_offset+cpio_end(payload[second_offset:])
        assert not any(payload[raw_end:])
    item = {'path': path, 'bytes': len(b), 'sha256': sha(b), 'header_fields': list(fields),
            'header_cmdline': b[64:576].split(b'\0')[0].decode(),
            'header_extra_cmdline_nonzero': any(b[608:1632]),
            'wrapped_kernel_bytes': ks, 'wrapped_kernel_sha256': sha(k),
            'LK_selected_DT_gzip_relative_offset': selected_dt,
            'LK_selected_DT_sha256': selected_fdt['sha256'],
            'LK_copied_DT_tail_bytes': copied_tail,
            'wrapped_ramdisk_bytes': rs, 'ramdisk_wrapper_first40': r[:40].hex(),
            'ramdisk_payload_bytes': len(payload), 'ramdisk_payload_sha256': sha(payload),
            'gzip_first_member_bytes': used, 'gzip_expanded_bytes': len(raw),
            'gzip_first_member_cpio_trailer_end_expanded': cpio_end(raw),
            'raw_deflate_EOS_payload_offset_exclusive': eos,
            'raw_deflate_eof_with_2MiB_payload': partial_raw.eof,
            'gzip_first_member_eof_with_2MiB_input': short.eof,
            'gzip_expanded_bytes_from_2MiB_input': len(expanded),
            'first_gzip_shortfall_at_2MiB': max(0, used-0x200000),
            'second_raw_cpio_offset': second_offset, 'required_through_cpio_trailer': raw_end or used,
            'modeled_successful_LK_handoff': {'payload_start': hex(ra), 'payload_end_exclusive': hex(ra+len(payload)),
                'copy_bytes': len(payload), 'initrd_start_be32': S.pack('>I', ra).hex(),
                'initrd_end_be32': S.pack('>I', ra+len(payload)).hex(),
                'margin_to_ram_console': 0x44400000-ra-len(payload),
                'not_observed_runtime': True}}
    assert len(item['header_cmdline']) <= 99 and not item['header_extra_cmdline_nonzero']
    assert not any(t.startswith('initrd=') for t in item['header_cmdline'].split())
    images[label] = item
    if label == 'failed_rescue':
        assert sha(b+bytes(16740352-len(b))) == '3f99c785cca60bf56c2505711e2d26b72623daf28180515d44c5ba2abf03a44a'

image, used, tail = gz(original_kernel[512:])
dt, props = dt_parse(tail)
assert len(tail) == dt['header'][1] == 62482
staticargs = props['/chosen', 'bootargs'].rstrip(b'\0').decode()
assert 'initrd=0x44000200,0x200000' in staticargs
assert ('/chosen', 'linux,initrd-start') not in props and ('/chosen', 'linux,initrd-end') not in props
textoff, imagesize = S.unpack_from('<QQ', image, 8)
kernel = {'expanded_bytes': len(image), 'expanded_sha256': sha(image), 'Image_header_hex': image[:64].hex(),
          'text_offset': hex(textoff), 'image_size': imagesize, 'nominal_end': hex(0x40080000+imagesize),
          'gzip_bytes': used, 'FDT_offset_in_wrapped_kernel': 512+used, 'FDT': dt,
          'IKCONFIG_present': b'IKCFG_ST' in image}

# Decode and cross-check every exact stock symbol, preserving only selected slices.
b = image; runs = []; start = None
for i in range(0, len(b)-7, 8):
    v = S.unpack_from('<Q', b, i)[0]
    if v >> 32 == 0xffffffc0:
        if start is None: start = i
    else:
        if start is not None and i-start > 400000: runs.append((start, i))
        start = None
assert len(runs) == 1
a, e = runs[0]; n = (e-a)//8; num = align(e, 256)
assert S.unpack_from('<Q', b, num)[0] == n == 70337
addresses = S.unpack_from('<'+'Q'*n, b, a); assert list(addresses) == sorted(addresses)
names = align(num+8, 256); p = names; encoded = []; markers = []
for i in range(n):
    if i % 256 == 0: markers.append(p-names)
    size = b[p]; assert 0 < size < 128
    encoded.append(b[p+1:p+1+size]); p += size+1
mo = align(p, 256); assert list(S.unpack_from('<'+'Q'*len(markers), b, mo)) == markers
to = align(mo+8*len(markers), 256); p = to; tokens = []; idx = []
for _ in range(256):
    idx.append(p-to); end = b.index(0, p); tokens.append(b[p:end].decode()); p = end+1
io = align(p, 256); assert list(S.unpack_from('<256H', b, io)) == idx
symbols = []
for addr, enc in zip(addresses, encoded):
    text = ''.join(tokens[t] for t in enc); assert re.fullmatch(r'[a-zA-Z?][a-zA-Z0-9_.$@]+', text)
    symbols.append((addr, text[1:]))
sym = {name: addr for addr, name in symbols}; base = sym.get('_text', 0xffffffc000080000)
rev = {addr: name for addr, name in symbols}
selected = ['setup_arch', 'early_init_dt_scan', 'early_init_dt_scan_nodes', 'early_init_dt_scan_chosen',
            'early_initrd', 'parse_early_param', 'do_early_param', 'populate_rootfs', 'unpack_to_rootfs', 'gunzip',
            'initrd_start', 'initrd_end', '__setup_start', '__setup_end', 'boot_command_line']
md = Cs(CS_ARCH_ARM64, CS_MODE_ARM); lines = []; facts = {}
for name in selected:
    if name not in sym: continue
    addr = sym[name]; off = addr-base; size = min(v for v in addresses if v > addr)-addr
    facts[name] = {'address': hex(addr), 'image_offset': off, 'next_symbol_delta': size}
    if name in ('initrd_start', 'initrd_end', '__setup_start', '__setup_end', 'boot_command_line'): continue
    assert 0 <= off < len(b) and 0 < size <= 16384
    code = b[off:off+size]; facts[name]['sha256'] = sha(code)
    lines.append(f'FUNCTION {name} {addr:#x} bytes={size}')
    for ins in md.disasm(code, addr):
        note = ''
        if ins.mnemonic in ('bl', 'b') and ins.op_str.startswith('#'):
            dest = int(ins.op_str[1:], 16); note = ' ; '+rev.get(dest, '?')
        lines.append(f'{ins.address:016x} {ins.bytes.hex()} {ins.mnemonic} {ins.op_str}{note}')
    lines.append('')
(O/'kernel.disasm').write_text('\n'.join(lines))
setups = []
# KALLSYMS_ALL is not presumed: discover the actual setup tuple by its exact fn pointer.
for match in re.finditer(re.escape(S.pack('<Q', sym['early_initrd'])), b):
    pos = match.start()-8
    if pos < 0 or pos % 8: continue
    strptr, fn, early = S.unpack_from('<QQi', b, pos)
    off = strptr-base
    if 0 <= off < len(b) and b[off:off+7] == b'initrd\0':
        setups.append({'record': hex(base+pos), 'name': 'initrd', 'function': hex(fn), 'early': early})
assert len(setups) == 1 and int(setups[0]['function'], 16) == sym['early_initrd'] and setups[0]['early'] == 1
compiled_literals = {}
for name, addr in [('initrd_start_name',0xffffffc000e88de8),('initrd_end_name',0xffffffc000e88e00),
                   ('fallback_config_cmdline',0xffffffc000e88e18),('bootargs_name',0xffffffc000dc3d18)]:
    off = addr-base
    compiled_literals[name] = {'address':hex(addr),'text':b[off:b.index(0,off)].decode()}
assert compiled_literals['initrd_start_name']['text'] == 'linux,initrd-start'
assert compiled_literals['initrd_end_name']['text'] == 'linux,initrd-end'
assert compiled_literals['bootargs_name']['text'] == 'bootargs'

# Revalidate existing reachable LK disassembly against exact bytes, no re-running its generators.
lk = read('2026-11-05-asus-boot-access-audit/sources/firmware/lk.bin', 'c5b5017ee3efdf018d9b6be7db978f29365c30e60a3fb9173660fda699f7b765')
for saved in ('initial','verify'):
    saved_lk = read(f'2026-11-05-asus-boot-access-audit/artifacts/device-backup/{saved}/lk.bin')
    assert saved_lk[:len(lk)] == lk and not any(saved_lk[len(lk):])
dis = read('2026-11-06-asus-full-boot-lk-contract/evidence/reachable-disassembly.txt', maxbytes=1024**2).decode()
ranges = [(0x41e04218,0x41e04296),(0x41e049e0,0x41e04a90),(0x41e1de90,0x41e1deee),
          (0x41e1df32,0x41e1df5c),(0x41e1e006,0x41e1e070),(0x41e1ce78,0x41e1ceaa),
          (0x41e1d0ee,0x41e1d180),(0x41e1d64e,0x41e1d698)]
out = []; count = 0
for line in dis.splitlines():
    m = re.match(r'^([0-9a-f]{8}) ([0-9a-f]+) ', line)
    if not m: continue
    addr = int(m[1], 16); code = bytes.fromhex(m[2]); off = addr-0x41e00000+512
    assert lk[off:off+len(code)] == code
    count += 1
    if any(lo <= addr < hi for lo, hi in ranges): out.append(line)
(O/'lk-excerpts.disasm').write_text('\n'.join(out)+'\n')
# Existing setter excerpt: validate all retained instruction bytes too.
setter = read('2026-11-06-asus-lk-linux49-handoff/evidence/handoff-disassembly.txt', maxbytes=1024**2).decode()
setter_lines = []
for line in setter.splitlines():
    m = re.match(r'^([0-9a-f]{8}) ([0-9a-f]+) ',line)
    if m and 0x41e26c28 <= int(m[1],16) < 0x41e26cb0:
        addr = int(m[1],16); code = bytes.fromhex(m[2]); off = addr-0x41e00000+512
        assert lk[off:off+len(code)] == code
        setter_lines.append(line)
with (O/'lk-excerpts.disasm').open('a') as f: f.write('\nSETTER existing-property replacement (bounded excerpt)\n'+'\n'.join(setter_lines)+'\n')
def lkstr(addr):
    off = addr-0x41e00000+512
    return lk[off:off+2048].split(b'\0')[0].decode()
assert S.unpack_from('<H', lk, 0x41e1de78-0x41e00000+512+4)[0]*2+0x41e1de78 == 0x41e1e006
lkfacts = {'all_reachable_instructions_byte_checked': count, 'recovery_mode_2_target': '0x41e1e006',
           'initial_cmdline': lkstr(0x41e5b964), 'DT_property_name_literals': {},
           'runtime_cmdline_providers_not_evaluated': True}
for pc, literal in [(0x41e1d0fa,0x41e1da6c),(0x41e1d11c,0x41e1da70),
                    (0x41e1d160,0x41e1da74),(0x41e1d662,0x41e1db84)]:
    delta = S.unpack_from('<I', lk, literal-0x41e00000+512)[0]
    addr = (pc+4+delta)&0xffffffff
    lkfacts['DT_property_name_literals'][hex(pc)] = {'address': hex(addr), 'text': lkstr(addr)}
assert [v['text'] for v in lkfacts['DT_property_name_literals'].values()] == ['/chosen','linux,initrd-start','linux,initrd-end','bootargs']
assert not any(t.startswith('initrd=') for t in lkfacts['initial_cmdline'].split())

# Retain only relevant public 3.18 reference excerpts, explicitly not exact build identity.
prefix = '2026-11-05-asus-latest-android-feasibility/sources/asus-original/kernel-3.18/'
excerpts = []
for rel, ranges in [('arch/arm64/mm/init.c', [(50,67),(183,193)]),
                    ('arch/arm64/kernel/setup.c', [(306,321),(372,398)]),
                    ('drivers/of/fdt.c', [(725,748),(896,963),(1046,1068)]),
                    ('init/main.c', [(420,464)]), ('init/initramfs.c', [(619,690)]),
                    ('lib/decompress_inflate.c', [(30,43),(83,122),(129,169)])]:
    src = read(prefix+rel, maxbytes=256*1024).decode().splitlines()
    excerpts.append('SOURCE '+prefix+rel+' SHA256 '+pins[prefix+rel]['sha256'])
    for lo, hi in ranges:
        excerpts.extend(f'{i}: {src[i-1]}' for i in range(lo,min(hi,len(src))+1))
(O/'source-excerpts.txt').write_text('\n'.join(excerpts)+'\n')
report = {'images': images, 'kernel': kernel, 'kernel_symbols': facts, 'exact_early_initrd_registration': setups,
          'compiled_literals':compiled_literals,
          'kallsyms': {'count': n, 'all_names_markers_token_indices_valid': True}, 'LK': lkfacts,
          'limits': {'CPU_seconds':60, 'input_per_file_max_bytes':32*1024**2,
                     'decompression_max_bytes':32*1024**2, 'no_full_kernel_or_ramdisk_written':True}}
(O/'audit.json').write_text(json.dumps(report, indent=2)+'\n')
for rel, pin in pins.items(): assert sha((W/rel).read_bytes()) == pin['sha256']
(O/'input-pins.json').write_text(json.dumps(pins, indent=2)+'\n')
assert sum(p.stat().st_size for p in R.rglob('*') if p.is_file()) < 1024**2
print(json.dumps({'status':'PASS', 'images':{k:{x:v[x] for x in ('ramdisk_payload_bytes','gzip_first_member_bytes','gzip_first_member_eof_with_2MiB_input','modeled_successful_LK_handoff')} for k,v in images.items()},'kernel_functions': facts,'output_bytes':sum(p.stat().st_size for p in R.rglob('*') if p.is_file())}, indent=2))
