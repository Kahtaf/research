"""One offline execution of the exact R2 assembly on marker-only stock DT.

The existing R2 unit fixture supplies synthetic kernel placement and OEM geometry.
This is a DT admission feasibility test, not a linked stock entry/loader proof.
"""
from pathlib import Path
import collections
import hashlib
import json
import re
import struct
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT.parent
assert not (ROOT / 'evidence/focused-check.json').exists(), 'One execution only'


def boundary(event, args):
    if event == 'open':
        assert not any(x in str(args[0]) for x in (
            '/private/', '/device-backup/', 'root_shell_wifi.py', 'mtk-su-mirror-b', '/dev/'))
    if event.startswith(('socket.', 'subprocess.')) or event in ('os.system', 'os.posix_spawn'):
        raise RuntimeError(event)


sys.addaudithook(boundary)
from elftools.elf.elffile import ELFFile
from unicorn import Uc, UC_ARCH_ARM64, UC_MODE_ARM, UC_HOOK_CODE, UC_HOOK_MEM_WRITE, UC_HOOK_MEM_READ
from unicorn.arm64_const import *
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM

sys.path.insert(0, str(WORK / '2026-11-06-asus-full-boot-lk-contract/scripts'))
import fdt
sys.path.insert(0, str(WORK / '2026-11-07-asus-stock-kernel-version-control/source'))
import bootformat as b
import kallsyms

sha = lambda v: hashlib.sha256(v).hexdigest()
original = (ROOT / 'source/stock.dtb').read_bytes()
h, nodes, tokens = fdt.parse(original)
assert nodes['']['compatible'] == b'mediatek,mt8163\0'
stream = bytearray()
replacement = b'mediatek,mt8163\0asus,p00a\0'
count = 0
for t, path, name, value, raw in tokens:
    if (t, path, name) == (3, '', 'compatible'):
        raw = raw[:4] + struct.pack('>I', len(replacement)) + raw[8:12] + replacement
        raw += bytes(-len(raw) % 4)
        count += 1
    stream += raw
assert count == 1
delta = len(stream) - h[9]
new_h = list(h)
new_h[1] += delta
new_h[3] += delta
new_h[9] = len(stream)
modified = struct.pack('>10I', *new_h) + original[40:h[2]] + stream + original[h[3]:]
_, after, after_tokens = fdt.parse(modified)
expected = {path: dict(props) for path, props in nodes.items()}
expected['']['compatible'] = replacement
assert after == expected
assert original[40:h[2]] == modified[40:new_h[2]]
assert original[h[3]:] == modified[new_h[3]:]
for a, z in zip(tokens, after_tokens):
    if (a[0], a[1], a[2]) != (3, '', 'compatible'):
        assert a == z
assert len(tokens) == len(after_tokens)
(ROOT / 'source/stock-marker-only.dtb').write_bytes(modified)
memory = nodes['/memory@00000000']['reg']
assert memory == struct.pack('>QQ', 0x40000000, 0x20000000)

asm = (ROOT / 'source/asus_entry_text.S').read_bytes()
assert sha(asm) == '32f22ec90acd2fc6787a15589ada5c2a1d06117768b43cc8ab88051c11cbfc5a'
BASE, FDT, RET = 0x40080000, 0x47000000, 0x44400000
with (ROOT / 'qa/unit.o').open('rb') as handle:
    elf = ELFFile(handle)
    symtab = elf.get_section_by_name('.symtab')
    alloc = {}
    address = BASE
    for i, section in enumerate(elf.iter_sections()):
        if section['sh_flags'] & 2:
            address = (address + 4095) & ~4095
            alloc[i] = address, bytearray(section.data())
            address += len(section.data())

    def symbol(s):
        idx = s['st_shndx']
        return s['st_value'] + (alloc[idx][0] if isinstance(idx, int) else 0)

    syms = {s.name: symbol(s) for s in symtab.iter_symbols()
            if s.name and s['st_shndx'] != 'SHN_UNDEF'}
    for section in elf.iter_sections():
        if section['sh_type'] != 'SHT_RELA':
            continue
        target, buf = alloc[section['sh_info']]
        for relocation in section.iter_relocations():
            off = relocation['r_offset']
            pc = target + off
            value = symbol(symtab.get_symbol(relocation['r_info_sym'])) + relocation['r_addend']
            word = struct.unpack_from('<I', buf, off)[0]
            kind = relocation['r_info_type']
            if kind == 275:
                imm = ((value >> 12) - (pc >> 12)) & 0x1fffff
                word = (word & ~((3 << 29) | (0x7ffff << 5))) | ((imm & 3) << 29) | ((imm >> 2) << 5)
            elif kind == 277:
                word = (word & ~(0xfff << 10)) | ((value & 0xfff) << 10)
            else:
                raise AssertionError(('Unexpected relocation', kind))
            struct.pack_into('<I', buf, off, word)
    code = bytes(alloc[elf.get_section_index('.text')][1])

cs = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
instructions = list(cs.disasm(code, BASE))
end = syms['asus_entry_text_end']
entry = [i for i in instructions if i.address < end]
for i in entry:
    assert not re.search(r'\b(?:sp|[xw](?:[1-3]|1[89]|2[0-9]|30))\b', i.op_str)
    assert i.mnemonic not in ('bl', 'blr', 'ret', 'stp', 'ldp')
    assert not re.match(r'[xw]0\b', i.op_str) or i.mnemonic in ('cmp', 'tst')
commit = syms['asus_entry_text_commit']
assert code[commit-BASE:commit-BASE+8] == bytes.fromhex('913800b99f3f03d5')
(ROOT / 'qa/unit.text.bin').write_bytes(code)
(ROOT / 'qa/unit.disasm').write_text(''.join(
    f'{i.address:#x} {i.bytes.hex()} {i.mnemonic} {i.op_str}\n' for i in instructions))

u = Uc(UC_ARCH_ARM64, UC_MODE_ARM)
for address, buf in alloc.values():
    u.mem_map(address, (len(buf) + 4095) & ~4095)
    u.mem_write(address, bytes(buf))
u.mem_map(FDT, (len(modified) + 4095) & ~4095)
u.mem_write(FDT, modified)
u.mem_map(RET, 0x80000)
incoming = bytearray(b'P' * 0x80000)
struct.pack_into('<7I', incoming, 0, 0x43474244, 64, 192, 128, 320, 576, 256)
struct.pack_into('<6I', incoming, 0x28, *([0xffffffff] * 6))
u.mem_write(RET, bytes(incoming))
regs = [UC_ARM64_REG_X0+i for i in range(29)] + [UC_ARM64_REG_X29, UC_ARM64_REG_X30]
for n, reg in enumerate(regs):
    u.reg_write(reg, FDT if n == 0 else 0x123400000000+n)
u.reg_write(UC_ARM64_REG_SP, 0x76543000)
mrs = {i.address: i for i in entry if i.mnemonic == 'mrs'}
trace = collections.deque(maxlen=12)
writes = []
steps = 0


def instruction(uc, address, size, data):
    global steps
    steps += 1
    trace.append((address, uc.reg_read(UC_ARM64_REG_X12),
                  uc.reg_read(UC_ARM64_REG_X13), uc.reg_read(UC_ARM64_REG_X16)))
    if address in mrs:
        uc.reg_write(UC_ARM64_REG_X4, 4 if 'currentel' in mrs[address].op_str.lower() else 0)
        uc.reg_write(UC_ARM64_REG_PC, address+4)


def write(uc, access, address, size, value, data):
    writes.append((address, size, value))


def read(uc, access, address, size, value, data):
    if FDT <= address < FDT + ((len(modified)+4095) & ~4095):
        assert address + size <= FDT + len(modified)


u.hook_add(UC_HOOK_CODE, instruction)
u.hook_add(UC_HOOK_MEM_WRITE, write)
u.hook_add(UC_HOOK_MEM_READ, read)
u.emu_start(BASE, end, count=2000000)
assert u.reg_read(UC_ARM64_REG_PC) == end
assert not writes and bytes(u.mem_read(RET, 0x80000)) == incoming
for n in (0, 1, 2, 3, *range(18, 31)):
    assert u.reg_read(regs[n]) == (FDT if n == 0 else 0x123400000000+n)
assert u.reg_read(UC_ARM64_REG_SP) == 0x76543000
lookup = {i.address: i for i in instructions}
last = lookup[trace[-1][0]]
previous = lookup[trace[-2][0]]
assert previous.mnemonic == 'cmp' and previous.op_str == 'x13, x16'
assert last.mnemonic == 'b.ne' and last.op_str == f'#{end:#x}'
assert trace[-1][2:] == (0x20000000, 0x7d600000)

donor_path = WORK / '2026-11-07-asus-stock-legacy-ram-usb-reporter/artifacts/candidate.img'
donor = donor_path.read_bytes()
header, kernel, ramdisk, tail = b.parse_image(donor)
raw, dt = b.ungzip(kernel[512:])
assert sha(donor) == 'dc0b98e66798e3abc019f454921b1c84ff3ce58e356e26d0785e05b7714d3427'
assert sha(raw) == 'db90ee7fff379f35ac2b0aafb11a6abee7b2c283b57d352c40ae7c6d7c35eb2a'
assert original == dt
symbols, sym, base, addresses = kallsyms.decode(raw)
assert base == 0xffffffc000080000
first = list(cs.disasm(raw[:4], base))[0]
assert first.mnemonic == 'b' and first.op_str == '#0xffffffc000080040'
assert sym['ram_console_early_init'] == 0xffffffc000f41350
clear_pc = 0xffffffc000f41564
clear = raw[clear_pc-base:clear_pc-base+4]
clear_instruction = list(cs.disasm(clear, clear_pc))[0]
assert clear_instruction.mnemonic == 'bl' and clear_instruction.op_str == '#0xffffffc00008a688'
cpio, extra = b.ungzip(ramdisk[512:])
assert not extra
helper = b.parse_cpio(cpio)['init'][3]
assert sha(helper) == '631a0aa5e72ee4110357ddac12bc5e5436ef3b1924cf64355f6fae99dc96d272'

result = dict(
    status='STOP_STOCK_MEMORY_CONTRACT_REFUSED', actual_emulation_cases=1,
    source_sha256=sha(asm), source_byte_identical_to_R2=True,
    fixture_object_sha256=sha((ROOT/'qa/unit.o').read_bytes()),
    original_stock_DT=dict(bytes=len(original), sha256=sha(original)),
    marker_only_DT=dict(bytes=len(modified), sha256=sha(modified),
                        compatible_before=repr(nodes['']['compatible']), compatible_after=repr(replacement),
                        every_other_property_token_and_memreserve_preserved=True),
    stock_memory_reg_hex=memory.hex(), stock_bank=['0x40000000', '0x60000000'],
    R2_required_bank=['0x40000000', '0xbd600000'],
    refusal=dict(pc=hex(last.address), bytes=last.bytes.hex(), instruction=f'{last.mnemonic} {last.op_str}',
                 compared_actual_size='0x20000000', compared_required_size='0x7d600000',
                 comparison_pc=hex(previous.address), comparison_bytes=previous.bytes.hex(),
                 retained_stores=len(writes), retained_region_byte_identical=True,
                 executed_instructions=steps),
    ABI=dict(x0_x3_x18_x30_SP_preserved=True, static_scratch_only_x4_x17_NZCV=True,
             calls_stack_mutable_globals_absent=True),
    fixture_limits=dict(kernel_text=hex(BASE), kernel_end=hex(syms['_end']),
                        placement='Synthetic existing R2 unit fixture, not actual stock extents',
                        FDT=hex(FDT), CurrentEL=4, SCTLR=0,
                        system_register_reads='Explicitly supplied by harness',
                        OEM_geometry='Synthetic valid existing R2 fixture'),
    donor_sha256=sha(donor), raw_sha256=sha(raw), helper_sha256=sha(helper),
    original_entry=dict(raw_offset=0, bytes=raw[:4].hex(),
                        virtual_target=first.op_str, physical_target_if_loaded_at_0x40080000='0x40080040',
                        patched=False, appended_writer_target=None),
    original_clear=dict(virtual_address=hex(clear_pc), raw_offset=hex(clear_pc-base),
                        bytes=clear.hex(), instruction=f'{clear_instruction.mnemonic} {clear_instruction.op_str}',
                        patched=False),
    no_candidate_no_installer_no_PLAN=True, no_stock_raw_or_boot_package_edits=True,
    scope=dict(device=False, network=False, SSH=False, cloud=False, private_inputs=False,
               VM_started=False, full_kernel_build=False, install=False, reboot=False, subagents=False),
    next_smallest_observable='Obtain public evidence of the exact /memory@00000000/reg bytes in the stock LK-delivered x0 FDT. The packaged stock DT fails; this unit does not assume that LK rewrites its bank to the R2 requirement. No new capture instrumentation or physical action is authorized here.',
)
(ROOT/'evidence/focused-check.json').write_text(json.dumps(result, indent=2)+'\n')
(ROOT/'evidence/refusal-trace.disasm').write_text(''.join(
    f'{pc:#x} {lookup[pc].bytes.hex()} {lookup[pc].mnemonic} {lookup[pc].op_str} '
    f'; x12={x12:#x} x13={x13:#x} x16={x16:#x}\n'
    for pc, x12, x13, x16 in trace))
print(json.dumps(result, indent=2))
