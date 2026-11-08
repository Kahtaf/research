#!/usr/bin/env python3
"""Offline intraprocedural reachability, not execution/emulation.

Decode only from entry/fallthrough/branch targets; never decode literal pools or
jump tables as instructions. Conditional edges are both retained. BL callees
are boundaries, not assumed successful. Table bounds come from preceding CMPs.
"""
from pathlib import Path
import hashlib
import json
import struct
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_ARM
from capstone.arm import *

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT.parent / '2026-11-05-asus-boot-access-audit/sources/firmware/lk.bin'
DATA = SOURCE.read_bytes()
assert hashlib.sha256(DATA).hexdigest() == 'c5b5017ee3efdf018d9b6be7db978f29365c30e60a3fb9173660fda699f7b765'
BASE = 0x41e00000
MD = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
MD.detail = True
ROOTS = {
    'bitness_selector': (0x41e02c74, 0x41e02cc8),
    'wrapper_parser': (0x41e04218, 0x41e04296),
    'normal_header': (0x41e042bc, 0x41e044e8),
    'normal_payload': (0x41e047e4, 0x41e04938),
    'recovery_header': (0x41e04564, 0x41e04770),
    'recovery_payload': (0x41e04980, 0x41e04ad2),
    'cmdline_append': (0x41e1ccbc, 0x41e1cd02),
    'aarch64_wrapper': (0x41e1ce30, 0x41e1ce5a),
    'byte_copy': (0x41e1ce64, 0x41e1ce78),
    'common_handoff': (0x41e1ce78, 0x41e1de1e),
    'handoff_wrapper': (0x41e1de3c, 0x41e1de4e),
    'boot_dispatch': (0x41e1de50, 0x41e1e0e2),
    'raw_inflate_wrapper': (0x41e1e378, 0x41e1e414),
    'gzip_header': (0x41e1e428, 0x41e1e4a0),
    'decompress_entry': (0x41e1e4a8, 0x41e1e4be),
    'case_insensitive_compare': (0x41e25d08, 0x41e25d5c),
    'ascii_lower': (0x41e252a0, 0x41e252ac),
}
TABLES = {0x41e02c96: (6, 1), 0x41e1de74: (10, 2), 0x41e1d5c8: (8, 2)}


def raw(addr, count):
    off = addr - BASE + 512
    assert 512 <= off <= len(DATA) - count
    return DATA[off:off + count]


result = {'kind': 'STATIC_REACHABILITY_UNION_NOT_RUNTIME_TRACE', 'functions': {}}
lines = []
for name, (start, end) in ROOTS.items():
    pending, seen, calls, exits = [start], {}, [], []
    while pending:
        addr = pending.pop()
        if addr in seen:
            continue
        if not start <= addr < end:
            exits.append(hex(addr))
            continue
        ins = next(MD.disasm(raw(addr, 4), addr, count=1))
        nxt = addr + ins.size
        edges = [nxt]
        if ins.id in (ARM_INS_B, ARM_INS_CBZ, ARM_INS_CBNZ):
            target = ins.operands[-1].imm
            edges = [target]
            if ins.id != ARM_INS_B or ins.cc not in (ARM_CC_AL, ARM_CC_INVALID):
                edges.append(nxt)
        elif ins.id in (ARM_INS_TBB, ARM_INS_TBH):
            count, width = TABLES[addr]
            tab = raw(addr + 4, count * width)
            values = list(tab) if width == 1 else struct.unpack('<' + 'H' * count, tab)
            edges = [addr + 4 + 2 * value for value in values]
        elif ins.id in (ARM_INS_BL, ARM_INS_BLX):
            target = ins.operands[0]
            calls.append({'address': hex(addr), 'target': hex(target.imm) if target.type == ARM_OP_IMM else ins.op_str})
        elif ins.id == ARM_INS_BX or ('pc' in ins.op_str and ins.id in (ARM_INS_POP, ARM_INS_LDM)):
            edges = []
        record = {'bytes': ins.bytes.hex(), 'instruction': ins.mnemonic + ' ' + ins.op_str, 'successors': [hex(x) for x in edges]}
        if ins.id == ARM_INS_LDR and len(ins.operands) > 1:
            op = ins.operands[1]
            if op.type == ARM_OP_MEM and op.mem.base == ARM_REG_PC:
                literal = ((addr + 4) & ~3) + op.mem.disp
                record['literal'] = {'address': hex(literal), 'word': hex(struct.unpack('<I', raw(literal, 4))[0])}
        seen[addr] = record
        pending.extend(edges)
    lines.append(f'FUNCTION {name} {start:08x} {end:08x}')
    for addr, rec in sorted(seen.items()):
        lines.append(f'{addr:08x} {rec["bytes"]:10} {rec["instruction"]:45} -> {",".join(rec["successors"])}' + (f' ; {rec["literal"]}' if 'literal' in rec else ''))
    result['functions'][name] = {'entry': hex(start), 'instructions': len(seen), 'calls': calls, 'external_tail_edges': sorted(set(exits))}

arm = Cs(CS_ARCH_ARM, CS_MODE_ARM)
smc = list(arm.disasm(raw(0x41e1b86c, 28), 0x41e1b86c))
arm_lines = [f'{i.address:08x} {i.bytes.hex()} {i.mnemonic} {i.op_str}' for i in smc]
arm_lines.append('41e1b8f4 ' + raw(0x41e1b8f4, 4).hex() + ' literal SMC function id 0x82000200')
(ROOT / 'evidence/smc-arm-disassembly.txt').write_text('\n'.join(arm_lines) + '\n')
(ROOT / 'evidence/reachable-disassembly.txt').write_text('\n'.join(lines) + '\n')
(ROOT / 'evidence/reachable-calls.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({name: f['instructions'] for name, f in result['functions'].items()}))
