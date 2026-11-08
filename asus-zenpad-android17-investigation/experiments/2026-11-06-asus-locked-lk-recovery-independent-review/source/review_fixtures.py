"""Bounded, local original-instruction review. No host device/network operations.

Reuses the pinned author's Unicorn scaffold and declared libc stubs, loading only
its definitions via AST (not its top-level fixture execution/output statements).
Additional fixtures join stages, execute runtime geometry lookup, inject failures,
and check transport/readback behavior. All storage/controller outcomes synthetic.
"""
from pathlib import Path
import ast
import hashlib
import json
import resource

ROOT = Path(__file__).resolve().parents[1]
scaffold = ROOT / 'source/emulate.py'
raw = scaffold.read_bytes()
assert hashlib.sha256(raw).hexdigest() == 'fb4738309a5ce1a0c844086886aa195f06e3bee234f1986bcc10b5c27d6957a3'
tree = ast.parse(raw, filename=str(scaffold))
end = next(i for i, n in enumerate(tree.body) if isinstance(n, ast.Expr) and isinstance(n.value, ast.Call) and isinstance(n.value.func, ast.Name) and n.value.func.id == 'lookup')
ns = {'__file__': str(scaffold), '__name__': 'review_scaffold_definitions'}
exec(compile(ast.Module(body=tree.body[:end], type_ignores=[]), str(scaffold), 'exec'), ns)
globals().update({k: v for k, v in ns.items() if not k.startswith('__')})

FLASH_RANGES = [(0x41e23338, 0x41e23754), (0x41e3ab9c, 0x41e3ac30),
                (0x41e21f24, 0x41e22046), (0x41e21844, 0x41e219f6),
                (0x41e2147c, 0x41e21496)]
STORAGE_RANGES = [(0x41e13e64, 0x41e13f30), (0x41e13fe4, 0x41e140f0),
                  (0x41e1416c, 0x41e141e0), (0x41e1b32c, 0x41e1b34a),
                  (0x41e1aca8, 0x41e1afac), (0x41e1911c, 0x41e192ca),
                  (0x41e17ea0, 0x41e17fbe)]
DEV, BLK, CARD, HOST, PTN = (0x43060000, 0x43061000, 0x43062000, 0x43063000, 0x43064000)


def geometry(f, start=160184, sectors=32696, area=8):
    f.allowed += STORAGE_RANGES
    fields = [(0x41e6b5ac, DEV), (DEV, 1), (DEV+8, BLK),
              (DEV+0x14, 0x41e1aca9), (DEV+0x18, 0x41e191f5),
              (BLK+0x14, 512), (BLK+0x68, 0x41e191cd), (BLK+0x64, 0x41e191a5),
              (CARD, HOST), (CARD+4, 30535680), (CARD+8, 512), (CARD+0x1c, 1),
              (0x41e78298, PTN), (PTN, start), (PTN+4, sectors),
              (PTN+8, area), (PTN+0x10, PTN+0x100)]
    for a, v in fields:
        f.put(a, v)
    f.u.mem_write(PTN+0x100, b'recovery\0')
    f.u.mem_write(BLK+0x18, b'\x09')
    f.u.mem_write(CARD+0x20, b'\x10\x00')
    f.u.mem_write(CARD+0x26a, b'\x20\x00')
    f.u.mem_write(CARD+0x133, b'\x10')
    f.u.mem_write(CARD+0x10c, b'\x07')
    f.hooks[0x41e17838] = lambda: f.ret(HOST)
    f.hooks[0x41e17848] = lambda: f.ret(CARD)
    def div():
        a, b, c, d = f.a()
        q, r = divmod(a+(b<<32), c+(d<<32))
        f.u.reg_write(UC_ARM_REG_R2, r & 0xffffffff)
        f.u.reg_write(UC_ARM_REG_R3, r >> 32)
        f.ret(q & 0xffffffff, q >> 32)
    f.hooks[0x41e38584] = div
    def command():
        host, p, *_ = f.a()
        assert host == HOST
        f.events.append({'mmc_command': f.word(p), 'argument': f.word(p+4)})
        f.ret(0)
    f.hooks[0x41e1785c] = command
    def status():
        f.put(f.a()[2], 0x800)
        f.ret(0)
    f.hooks[0x41e17d20] = status
    f.hooks[0x41e17804] = lambda: f.ret(0)
    def write():
        controller, sector, count, pointer = f.a()
        assert (controller, sector, count, pointer) == (0, start, N//512, BUF)
        f.events.append({'block_write': True, 'controller': controller,
                         'sector': sector, 'count': count,
                         'selected_area_bits': bytes(f.u.mem_read(CARD+0xff, 1))[0] & 7,
                         'sha256': hashlib.sha256(bytes(f.u.mem_read(pointer, count*512))).hexdigest()})
        f.ret(0)
    f.hooks[0x41e18360] = write


def flash_setup(f):
    f.allowed += FLASH_RANGES
    f.hooks[0x41e3a1c8] = lambda: f.ret()
    f.hooks[0x41e059ec] = lambda: f.ret(123)
    f.hooks[0x41e05a74] = lambda: f.ret(123)


def register(f):
    f.allowed += [(0x41e1ea08, 0x41e1ee30), (0x41e1e500, 0x41e1e55c)]
    for a in [0x41e1ca04, 0x41e1cae8, 0x41e001dc, 0x41e1e92c]:
        f.hooks[a] = lambda: f.ret()
    f.hooks[0x41e3aae4] = lambda: f.ret(1)
    f.hooks[0x41e3ab10] = lambda: f.ret(0)
    def warranty():
        f.put(f.a()[0], 0)
        f.ret()
    f.hooks[0x41e3a24c] = warranty
    f.hooks[0x41e1a7e8] = lambda: f.ret(0)
    f.stops.add(0x41e1ed56)
    f.call(0x41e1ea08, BUF)
    f.stops.remove(0x41e1ed56)
    slot = (f.word(0x41e1e538)+0x41e1e52a) & 0xffffffff
    return f.word(slot)


def dispatch_command(f, head, command, secure=1, security_check=1):
    f.allowed += [(0x41e1e7f4, 0x41e1e8ce), (0x41e1f288, 0x41e1f31e)]
    f.u.mem_write(0x41e701c0, command.encode()+b'\0')
    f.put(0x430f0000+12, head)
    for reg, value in [(UC_ARM_REG_R9, 0x41e701c0), (UC_ARM_REG_R5, 0x41e711c4),
                       (UC_ARM_REG_R8, 0x41e78434), (UC_ARM_REG_R11, 0x41e7842c)]:
        f.u.reg_write(reg, value)
    f.hooks[0x41e3b218] = lambda: f.ret(secure)
    f.hooks[0x41e392dc] = lambda: f.ret(security_check)
    f.stops.add(0x41e1e7bc)
    f.call(0x41e1e7f4)
    f.stops.remove(0x41e1e7bc)


def usb_reader(f, mode='complete'):
    # Execute the real LK 16 KiB request loop; mock queue/completion only.
    f.allowed += [(0x41e1e588, 0x41e1e62c), (0x41e22a24, 0x41e22eb8),
                  (0x41e2149c, 0x41e21598)]
    f.put(0x41e711c0, 0x43065000)
    f.put(0x41e78434, BUF)
    f.put(0x41e78440, BUF)
    counts = []
    def queue():
        _, req, *_ = f.a()
        dest, size = f.word(req), f.word(req+4)
        assert BUF <= dest < BUF+N and 0 < size <= 16384 and dest+size <= BUF+N
        sent = size if mode == 'complete' else (28 if mode == 'short' else 0)
        f.u.mem_write(dest, REC[dest-BUF:dest-BUF+sent])
        f.put(req+4, sent)
        counts.append({'requested': size, 'returned': sent, 'destination': hex(dest)})
        f.ret(-1 if mode == 'error' else 0)
    f.hooks[0x41e096dc] = queue
    f.hooks[0x41e1bec4] = lambda: f.ret(0)
    return counts


def joined():
    f = F()
    f.protocol()
    head = register(f)
    geometry(f)
    flash_setup(f)
    counts = usb_reader(f)
    dispatch_command(f, head, 'getvar:sofia_support')
    assert f.word(0x41e73358) == 1
    dispatch_command(f, head, 'download:00ff7000')
    assert f.word(0x41e7842c) == N
    dispatch_command(f, head, 'flash:recovery')
    assert f.responses() == ['OKAY', 'DATA00ff7000', 'OKAY', 'OKAY']
    assert sum(x['returned'] for x in counts) == N
    assert [e for e in f.events if 'mmc_command' in e] == [
        {'mmc_command': 35, 'argument': 160184}, {'mmc_command': 36, 'argument': 192879},
        {'mmc_command': 38, 'argument': 1}]
    writes = [e for e in f.events if 'block_write' in e]
    assert len(writes) == 1 and writes[0]['sha256'] == hashlib.sha256(REC).hexdigest()
    assert f.word(0x41e73358) == 1
    f.save('joined_registration_dispatch_setter_download_geometry_trim_write',
           usb_requests=len(counts), usb_bytes=N, max_usb_request=max(c['requested'] for c in counts),
           session_flag_after_flash=f.word(0x41e73358), runtime_geometry_synthetic=True)


def area_failure():
    f = F()
    f.protocol()
    geometry(f)
    flash_setup(f)
    f.put(0x41e73358, 1)
    f.u.mem_write(ARG, b'recovery\0')
    f.u.mem_write(BUF, REC)
    f.u.mem_write(CARD+0xff, b'\x01')
    def switch():
        f.events.append({'area_switch_failure': 4})
        f.ret(4)
    f.hooks[0x41e17de8] = switch
    f.call(0x41e23338, ARG, BUF, N)
    assert len([e for e in f.events if 'area_switch_failure' in e]) == 2
    assert not any('mmc_command' in e for e in f.events)
    assert next(e for e in f.events if 'block_write' in e)['selected_area_bits'] == 1
    assert f.responses() == ['OKAY']
    f.save('area_switch_fails_twice_but_block_write_attempted_and_stub_success_OKAY',
           physical_wrong_area_write_proven=False, block_completion_synthetic=True)


def geometry_drift():
    f = F()
    f.protocol()
    geometry(f, start=160185)
    flash_setup(f)
    f.put(0x41e73358, 1)
    f.u.mem_write(ARG, b'recovery\0')
    f.u.mem_write(BUF, REC)
    f.call(0x41e23338, ARG, BUF, N)
    assert [e['argument'] for e in f.events if 'mmc_command' in e] == [160185, 192880, 1]
    assert f.responses() == ['OKAY']
    f.save('runtime_geometry_shift_is_not_rejected_by_firmware')


def raw_writer_bounds(length):
    f = F()
    f.protocol()
    flash_setup(f)
    f.u.mem_write(ARG, b'recovery\0')
    f.u.mem_write(BUF, REC[:512])
    f.hooks[0x41e13fe4] = lambda: f.ret(9)
    f.hooks[0x41e14074] = lambda: f.ret(START, 0)
    f.hooks[0x41e14044] = lambda: f.ret(8)
    f.hooks[0x41e140b4] = lambda: f.ret(N, 0)
    def erased():
        f.events.append({'erase_reached': True})
        f.ret(0)
    f.hooks[0x41e141b8] = erased
    f.stops.add(0x41e1416c)
    f.call(0x41e21844, ARG, BUF, length)
    reached = f.u.reg_read(UC_ARM_REG_PC) == 0x41e1416c
    assert reached == (length == 0xfffffe01)
    f.save('raw_writer_roundup_'+hex(length), write_boundary_reached=reached,
           note='No huge buffer allocated, no write performed; stop before storage wrapper.')


def usb_failure(mode):
    f = F()
    f.protocol()
    counts = usb_reader(f, mode)
    f.u.mem_write(ARG, b'00ff7000\0')
    f.call(0x41e22a24, ARG, BUF, 0)
    assert f.word(0x41e711c4) == 3 and f.word(0x41e7842c) == N
    assert f.responses() == ['DATA00ff7000']
    f.save('actual_usb_loop_'+mode, requests=counts, published_length=N, state=3)


def setter_names():
    # Full name is the sole proposed command. Prefix/empty variants are negative
    # host-allowlist examples only; every case remains synthetic.
    for name, expected in [('product', 0), ('sofia_supportX', 0), ('sofia', 1), ('', 1)]:
        f = F()
        f.protocol()
        head = register(f)
        dispatch_command(f, head, 'getvar:'+name, secure=0, security_check=0)
        assert f.word(0x41e73358) == expected
        f.save('registered_getvar_'+repr(name)+'_nonsecure_secondary_zero', flag=expected)


def readback(mode):
    f = F()
    f.protocol()
    geometry(f)
    f.allowed += [(0x41e2284c, 0x41e22a10), (0x41e1efcc, 0x41e1efde)]
    f.u.mem_write(ARG, b' recovery\0')
    # Exact fixed command has a single ASCII space; these are declared libc stubs.
    f.hooks[0x41e25e00] = lambda: f.ret(f.a()[0])
    f.hooks[0x41e25c20] = lambda: f.ret(f.a()[0])
    f.hooks[0x41e25970] = lambda: f.ret(0x43070000)
    f.hooks[0x41e2599c] = lambda: f.ret()
    read_calls = []
    digest = hashlib.sha256()
    total = 0
    def read():
        area, _, lo, hi = f.a()
        sp = f.u.reg_read(UC_ARM_REG_SP)
        pointer, size = f.word(sp), f.word(sp+8)
        offset = lo+(hi<<32)
        assert area == 8 and START <= offset < START+N and offset+size <= START+N
        read_calls.append((offset, size))
        if mode == 'success':
            f.u.mem_write(pointer, REC[offset-START:offset-START+size])
            f.ret(size, 0)
        else:
            # Failure leaves the scratch buffer unchanged, as a real failed read may.
            f.ret(-1, 0xffffffff)
    f.hooks[0x41e14190] = read
    def send():
        nonlocal total
        pointer, size, *_ = f.a()
        b = bytes(f.u.mem_read(pointer, size))
        if size > 64:
            digest.update(b)
            total += size
        else:
            f.events.append({'protocol': b.decode('ascii')})
        f.ret(size)
    f.hooks[0x41e1e648] = send
    f.call(0x41e2284c, ARG, BUF, 0)
    assert total == N and f.responses() == ['OKAY']
    assert len(read_calls) == 512 and read_calls[-1] == (START+255*65536, 28672)
    assert (digest.hexdigest() == hashlib.sha256(REC).hexdigest()) == (mode == 'success')
    f.save('readback_'+mode, raw_bytes=total, sha256=digest.hexdigest(),
           read_calls=len(read_calls), unique_read_ranges=len(set(read_calls)),
           last_read=list(read_calls[-1]), all_reads_synthetic=True)


joined()
area_failure()
geometry_drift()
raw_writer_bounds(N+1)
raw_writer_bounds(0xfffffe00)
raw_writer_bounds(0xfffffe01)
usb_failure('short')
usb_failure('error')
setter_names()
readback('success')
readback('failure')

from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB
md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
lines = []
for addr, h in sorted(PINS.items()):
    a = int(addr, 16)
    b = bytes.fromhex(h)
    assert B[a-BASE+512:a-BASE+512+len(b)] == b
    decoded = list(md.disasm(b, a))
    assert len(decoded) == 1
    i = decoded[0]
    lines.append(f'{a:08x} {h:10} {i.mnemonic:10} {i.op_str}')
(ROOT/'evidence/review-instruction-pins.json').write_text(json.dumps(PINS, indent=2)+'\n')
(ROOT/'evidence/review-executed-disassembly.txt').write_text('\n'.join(lines)+'\n')
(ROOT/'evidence/review-fixtures.json').write_text(json.dumps({
    'cases': RESULTS, 'case_count': len(RESULTS), 'instruction_pins': len(PINS),
    'peak_rss_bytes_macos': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    'all_IO_synthetic': True, 'device_operations': False,
    'limits': {'per_call_instructions': 100000, 'per_call_timeout_us': 2000000,
               'mapped_bytes': 0x2200000, 'cpu_instances_concurrent': 1},
    'scaffold_sha256': hashlib.sha256(raw).hexdigest()
}, indent=2)+'\n')
print(f'{len(RESULTS)} review cases passed; {len(PINS)} original instructions verified')
