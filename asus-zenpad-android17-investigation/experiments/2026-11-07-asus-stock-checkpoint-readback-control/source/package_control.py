"""One bounded stock diagnostic patch and actual-artifact preservation check."""
from pathlib import Path
import ast
import difflib
import gzip
import json
import struct
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT.parent
assert not (ROOT / 'evidence/packaging-receipt.json').exists(), 'One packaging/check only'


def boundary(event, args):
    if event == 'open':
        assert not any(s in str(args[0]) for s in (
            '/private/', '/device-backup/', 'root_shell_wifi.py', 'mtk-su-mirror-b', '/dev/'))
    if event.startswith(('subprocess.', 'socket.')) or event in ('os.system', 'os.posix_spawn'):
        raise RuntimeError(event)


sys.addaudithook(boundary)
sys.path.insert(0, str(WORK / '2026-11-07-asus-stock-kernel-version-control/source'))
import bootformat as b
import kallsyms
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM

sha = b.sha
DONOR = WORK / '2026-11-07-asus-stock-legacy-ram-usb-reporter'
PREVIOUS = WORK / '2026-11-07-asus-stock-scalar-checkpoint-control'
for name in ('artifacts', 'evidence'):
    (ROOT / name).mkdir(exist_ok=True)
data = (DONOR / 'artifacts/candidate.img').read_bytes()
assert sha(data) == 'dc0b98e66798e3abc019f454921b1c84ff3ce58e356e26d0785e05b7714d3427'
header, kernel, ramdisk, trailing = b.parse_image(data)
assert not trailing
raw, dt = b.ungzip(kernel[512:])
assert sha(raw) == 'db90ee7fff379f35ac2b0aafb11a6abee7b2c283b57d352c40ae7c6d7c35eb2a'
symbols, sym, base, addresses = kallsyms.decode(raw)
WRAPPER = 0xffffffc000695368
SETTER = 0xffffffc0006976c8
GETTER = 0xffffffc0006976f0
PRINTK = 0xffffffc000abe7a8
CALL = 0xffffffc000800278
FORMAT = 0xffffffc000e37a38
assert base == 0xffffffc000080000
for name, address in (('aee_rr_show_fiq_step', WRAPPER), ('aee_rr_rec_fiq_step', SETTER),
                      ('aee_rr_curr_fiq_step', GETTER), ('printk', PRINTK),
                      ('mtk_arch_reset_handle', 0xffffffc000800260)):
    assert sym[name] == address
slot_end = next(a for a in addresses if a > WRAPPER)
assert slot_end - WRAPPER == 48


def old_at(address, length):
    return raw[address-base:address-base+length]


assert sha(old_at(WRAPPER, 48)) == '8a0b7dd9bcfe10d8d2909e048f0ba6e87dcb084eb53a700764648760558b94dd'
assert sha(old_at(SETTER, 40)) == 'a35af0be81b2b827c8339dd9a8c92617b499644b23ee084af7a54ceb45bf8bd5'
assert sha(old_at(GETTER, 32)) == '7e46a348165e281054eadd2710f9a46e28e47bffd05eccd3930d78b797001093'
original_format = b' fiq step: %u \0'
assert old_at(FORMAT, len(original_format)) == original_format
# Same 15-byte NUL span. Priority 1 matches the physically observed replaced log.
new_format = b'\x011A7_READ=%u \n\0'
assert len(new_format) == len(original_format) == 15


def bl(pc, target):
    delta = target - pc
    assert delta % 4 == 0 and -(1 << 27) <= delta < (1 << 27)
    return 0x94000000 | ((delta // 4) & 0x3ffffff)


def adrp(pc, target, register):
    delta = (target >> 12) - (pc >> 12)
    assert -(1 << 20) <= delta < (1 << 20)
    immediate = delta & 0x1fffff
    return 0x90000000 | ((immediate & 3) << 29) | ((immediate >> 2) << 5) | register


words = [
    0xa9bf7bfd,                         # stp x29,x30,[sp,#-16]!
    0x910003fd,                         # mov x29,sp
    0x52800000 | (167 << 5),             # mov w0,#167
    bl(WRAPPER + 12, SETTER),
    bl(WRAPPER + 16, GETTER),
    0x2a0003e1,                         # mov w1,w0 (actual current value)
    adrp(WRAPPER + 24, FORMAT, 0),
    0x91000000 | ((FORMAT & 0xfff) << 10),  # add x0,x0,#format_page_offset
    bl(WRAPPER + 32, PRINTK),
    0xa8c17bfd,                         # ldp x29,x30,[sp],#16
    0xd65f03c0,                         # ret
]
wrapper = struct.pack('<' + 'I' * len(words), *words)
assert len(wrapper) == 44 <= slot_end - WRAPPER
assert old_at(CALL, 4) == bytes.fromhex('4cf90a94')
patches = [
    (WRAPPER, old_at(WRAPPER, len(wrapper)), wrapper, 'diagnostic wrapper'),
    (CALL, old_at(CALL, 4), struct.pack('<I', bl(CALL, WRAPPER)), 'diagnostic log BL'),
    (FORMAT, original_format, new_format, 'same-length format NUL span'),
]
new = bytearray(raw)
allowed = set()
for address, old, value, purpose in patches:
    offset = address - base
    assert old == raw[offset:offset+len(old)] and len(old) == len(value)
    assert not allowed.intersection(range(offset, offset+len(value)))
    allowed.update(range(offset, offset+len(value)))
    new[offset:offset+len(value)] = value
changed = {i for i, (x, y) in enumerate(zip(raw, new)) if x != y}
assert len(new) == len(raw) and changed and changed <= allowed
# The last original RET and all adjacent code/data remain untouched.
assert new[WRAPPER-base+44:slot_end-base] == old_at(WRAPPER+44, 4)

md = Cs(CS_ARCH_ARM64, CS_MODE_ARM)


def disassemble(value, address):
    instructions = list(md.disasm(value, address))
    assert sum(i.size for i in instructions) == len(value)
    return instructions


expected = [
    ('stp', 'x29, x30, [sp, #-0x10]!'), ('mov', 'x29, sp'), ('mov', 'w0, #0xa7'),
    ('bl', f'#{SETTER:#x}'), ('bl', f'#{GETTER:#x}'), ('mov', 'w1, w0'),
    ('adrp', f'x0, #{FORMAT & ~0xfff:#x}'), ('add', 'x0, x0, #0xa38'),
    ('bl', f'#{PRINTK:#x}'), ('ldp', 'x29, x30, [sp], #0x10'), ('ret', ''),
]
decoded = disassemble(wrapper, WRAPPER)
assert [(i.mnemonic, i.op_str) for i in decoded] == expected
assert [(i.mnemonic, i.op_str) for i in disassemble(patches[1][2], CALL)] == [('bl', f'#{WRAPPER:#x}')]
# Exact bounded ABI sequence: only x0/x1 are assigned outside calls; x29/x30 are
# restored; 16-byte frame remains aligned across all three calls; w1 gets the
# getter result before x0 becomes printk's format. No direct scalar store added.
assert all(i.mnemonic not in ('str', 'strb', 'strh', 'stur') for i in decoded)
assert [i.address for i in decoded if i.mnemonic == 'bl'] == [WRAPPER+12, WRAPPER+16, WRAPPER+32]
handler_before = old_at(0xffffffc000800260, 72)
handler_after = bytes(new[0x780260:0x7802a8])
assert handler_after[:24] == handler_before[:24] and handler_after[28:] == handler_before[28:]
handler = disassemble(handler_after, 0xffffffc000800260)
by_address = {i.address: (i.mnemonic, i.op_str) for i in handler}
for address, instruction in {
    0xffffffc00080026c: ('add', 'x0, x0, #0x360'),
    0xffffffc000800270: ('str', 'x2, [x29, #0x10]'),
    0xffffffc000800274: ('str', 'x1, [x29, #0x18]'),
    0xffffffc00080027c: ('ldr', 'x2, [x29, #0x10]'),
    0xffffffc000800280: ('ldr', 'x1, [x29, #0x18]'),
    0xffffffc00080028c: ('bl', '#0xffffffc000800138'),
}.items():
    assert by_address[address] == instruction

stream = kernel[512:-len(dt)]
gz = bytearray(gzip.compress(bytes(new), compresslevel=9, mtime=0))
assert stream[:3] == gz[:3] and stream[3] == 0 and stream[8] == 2
gz[:10] = stream[:10]
new_kernel = b.wrap(kernel, bytes(gz) + dt)
image = b.make_image(header, new_kernel, ramdisk)
full = image + bytes(b.PARTITION_SIZE - len(image))

# Specialize only the parent's pins, length, profile and one allowed preimage.
original = (PREVIOUS / 'source/install.py').read_text()
current = 'b403e999805fcbbc76b988100cad5c49f13f5ca33fb70e99b555d6292e2107db'
line = next(x for x in original.splitlines() if x.startswith('INSTALL_PREIMAGES='))
assert current not in line
edits = {
    "IMAGE_SHA='ebc410fb95113d74c2b16fe7a56e398215b99fcad4f6c948946af49de7e07bc4'": f"IMAGE_SHA='{sha(image)}'",
    f"FULL_SHA='{current}'": f"FULL_SHA='{sha(full)}'",
    'len(image)==7745536': f'len(image)=={len(image)}',
    "profile='stock-3.18.35-scalar-a7-legacy-ram-usb-control-r1'": "profile='stock-3.18.35-a7-current-readback-legacy-ram-usb-control-r1'",
    line: line[:-1] + f",'{current}')",
}
installer = original
for old, value in edits.items():
    assert installer.count(old) == 1
    installer = installer.replace(old, value)


def block(source, name):
    node = next(n for n in ast.parse(source).body if getattr(n, 'name', None) == name)
    return ''.join(source.splitlines(True)[node.lineno-1:node.end_lineno])


for name in ('execute', 'Transport', 'Guard'):
    assert block(original, name) == block(installer, name)
reverse = installer
for old, value in reversed(list(edits.items())):
    assert reverse.count(value) == 1
    reverse = reverse.replace(value, old)
assert reverse == original
for name in ('adb', 'legacy_adb.py', 'bootformat.py'):
    value = (PREVIOUS / 'source' / name).read_bytes()
    (ROOT / 'source' / name).write_bytes(value)
    assert (ROOT / 'source' / name).read_bytes() == value
(ROOT / 'source/install.py').write_text(installer)
assert (ROOT / 'source/install.py').read_text() == installer
(ROOT / 'source/install.diff').write_text(''.join(difflib.unified_diff(
    original.splitlines(True), installer.splitlines(True), fromfile='scalar/install.py', tofile='readback/install.py')))
(ROOT / 'artifacts/candidate.img').write_bytes(image)
(ROOT / 'artifacts/candidate.p10.raw').write_bytes(full)

# Check the delivered bytes, including complete helper/ramdisk, DT, containers,
# and padding. All instructions outside the three explicit spans are identical.
actual_image = (ROOT / 'artifacts/candidate.img').read_bytes()
actual_full = (ROOT / 'artifacts/candidate.p10.raw').read_bytes()
assert actual_image == image and actual_full == full
ah, ak, ar, at = b.parse_image(actual_image)
nr, nd = b.ungzip(ak[512:])
assert nr == new and len(nr) == len(raw) and nd == dt and ar == ramdisk and not at
assert ah[:8] == header[:8] and ah[12:576] == header[12:576] and ah[608:] == header[608:]
assert ak[:4] == kernel[:4] and ak[8:512] == kernel[8:512]
ro = len(header) + b.align(len(ak))
assert not any(actual_image[len(header)+len(ak):ro])
assert not any(actual_image[ro+len(ar):]) and not any(actual_full[len(actual_image):])
assert len(actual_full) == b.PARTITION_SIZE
cpio, extra = b.ungzip(ar[512:])
assert not extra
init = b.parse_cpio(cpio)['init'][3]
elf = b.elf_static(init)


def rec(value):
    return dict(bytes=len(value), sha256=sha(value))


def listing(instructions):
    return '\n'.join(f'{i.address:#x} {i.bytes.hex()} {i.mnemonic} {i.op_str}' for i in instructions) + '\n'


word_changes = []
for address, old, value, purpose in patches[:2]:
    for offset in range(0, len(value), 4):
        before, after = old[offset:offset+4], value[offset:offset+4]
        if before != after:
            word_changes.append(dict(address=hex(address+offset), raw_offset=hex(address+offset-base),
                                     before=before.hex(), after=after.hex()))
receipt = dict(
    status='LOCAL_PACKAGED_NO_PHYSICAL_GO', expected_tag=167,
    candidate=rec(actual_image), full_p10=rec(actual_full), donor=rec(data),
    raw_before=rec(raw), raw_after=rec(nr), ramdisk=rec(ar), init=rec(init), init_elf=elf, dt=rec(nd),
    wrapper_slot_bytes=48, wrapper_bytes=44, raw_differing_bytes=len(changed),
    patches=[dict(address=hex(a), raw_offset=hex(a-base), before=o.hex(), after=v.hex(), purpose=p)
             for a, o, v, p in patches], changed_instruction_words=word_changes,
    format=dict(address=hex(FORMAT), bytes=len(new_format), escaped=repr(new_format),
                loglevel=1, expected_line='A7_READ=167 <newline>', value_source='aee_rr_curr_fiq_step return w0'),
    abi=dict(frame_bytes=16, sp_alignment_preserved=True, x29_x30_saved_restored=True,
             no_other_callee_saved_registers_written=True, reset_x1_x2_stores_reloads_unchanged=True,
             printk_return_unused=True, no_new_direct_field_store=True,
             setter_getter_unchanged=True, getter_is_current_not_saved=True),
    preservation=dict(raw_length=True, only_three_explicit_spans=True, wrapper_slot_tail=True,
        ramdisk_entire=True, helper_ELF=True, appended_DT=True, header_addresses_bootargs=True,
        header_except_kernel_length_ID=True, kernel_wrapper_except_length=True,
        zero_container_partition_padding=True, execute_Transport_Guard_byte_identical=True,
        legacy_adapters_byte_identical=True, installer_only_five_specializations=True,
        original_admissions_preserved=True, current_physical_preimage_appended=current),
    gzip_header_before=stream[:10].hex(), gzip_header_after=bytes(gz[:10]).hex(),
    gzip_settings='level 9; original ten-byte metadata; fixed raw kernel length',
    physical_first_result_sha256=sha((WORK / '2026-11-07-asus-stock-scalar-checkpoint-trial/evidence/RESULT.json').read_bytes()),
    installer_sha256=sha(installer.encode()), installer_parent_sha256=sha(original.encode()),
    limits='No physical/OS flash GO. No retention fix assumed. Before-reset 0 may be setter guard/no-store; missing log UNKNOWN. Logging may affect visibility/timing. No 4.9 nonexecution inference.',
    scope=dict(device=False, network=False, private_inputs=False, kernel_compile=False,
               VM_startup=False, install=False, reboot=False, subagents=False),
)
(ROOT / 'evidence/diagnostic-wrapper.disasm').write_text(listing(decoded))
(ROOT / 'evidence/reset-handler.disasm').write_text(listing(handler))
(ROOT / 'evidence/setter-current-getter.disasm').write_text(
    listing(disassemble(old_at(SETTER, 40), SETTER)) + listing(disassemble(old_at(GETTER, 32), GETTER)))
(ROOT / 'evidence/packaging-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps(receipt, indent=2))
