#!/usr/bin/env python3
"""Candidate references only. Raw exact LK bytes; no network or target operations."""
import collections
import hashlib
import json
from pathlib import Path
import struct
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB
from capstone.arm import *

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT.parent / '2026-11-05-asus-boot-access-audit/sources/firmware/lk.bin'
data = SOURCE.read_bytes()
source_sha = hashlib.sha256(data).hexdigest()
assert source_sha == 'c5b5017ee3efdf018d9b6be7db978f29365c30e60a3fb9173660fda699f7b765'
BASE = 0x41e00000
needles = ['initrd', 'ramdisk', 'decompress', 'boot_linux', 'kernel_addr',
           'device tree', 'booting linux', '64 bit kernel', 'kernel address']
decoder = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
decoder.detail = True
decoder.skipdata = True
registers = {}
history = collections.deque(maxlen=12)
results = []


def read32(address):
    offset = address - BASE + 512
    return struct.unpack_from('<I', data, offset)[0] if 512 <= offset <= len(data) - 4 else None


def string(address):
    if address is None:
        return None
    offset = address - BASE + 512
    if not 512 <= offset < len(data):
        return None
    value = data[offset:offset + 240].split(b'\0')[0]
    if len(value) > 4 and all(32 <= c < 127 or c in (10, 13) for c in value):
        return value.decode()
    return None


def operand_value(operand, pc):
    if operand.type == ARM_OP_IMM:
        return operand.imm
    if operand.type == ARM_OP_REG:
        return pc if operand.reg == ARM_REG_PC else registers.get(operand.reg)
    return None


for instruction in decoder.disasm(data[512:0x41000], BASE):
    history.append(f'{instruction.address:08x} {instruction.bytes.hex()} {instruction.mnemonic} {instruction.op_str}')
    if not instruction.id:
        registers.clear()
        continue
    ops = instruction.operands
    pc = instruction.address + 4
    written = value = None
    if instruction.id == ARM_INS_LDR and len(ops) > 1 and ops[1].type == ARM_OP_MEM:
        mem = ops[1].mem
        base = pc & ~3 if mem.base == ARM_REG_PC else registers.get(mem.base)
        index = registers.get(mem.index) if mem.index else 0
        if base is not None and index is not None:
            value = read32((base + index + mem.disp) & 0xffffffff)
        written = ops[0].reg
    elif instruction.id in (ARM_INS_MOV, ARM_INS_MOVW) and len(ops) > 1:
        written, value = ops[0].reg, operand_value(ops[1], pc)
    elif instruction.id == ARM_INS_MOVT:
        written = ops[0].reg
        old = registers.get(written)
        if old is not None:
            value = (old & 65535) | (ops[1].imm << 16)
    elif instruction.id in (ARM_INS_ADD, ARM_INS_SUB) and len(ops) >= 2:
        written = ops[0].reg
        x, y = ((operand_value(ops[1], pc), operand_value(ops[2], pc)) if len(ops) >= 3
                else (registers.get(written), operand_value(ops[1], pc)))
        if x is not None and y is not None:
            value = (x + y if instruction.id == ARM_INS_ADD else x - y) & 0xffffffff
    for changed in instruction.regs_access()[1]:
        registers.pop(changed, None)
    if written is not None and value is not None:
        registers[written] = value
    if instruction.id in (ARM_INS_BL, ARM_INS_BLX):
        args = {f'r{i}': {'value': registers.get(ARM_REG_R0 + i),
                          'string': string(registers.get(ARM_REG_R0 + i))} for i in range(4)}
        if any(a['string'] and any(n in a['string'].lower() for n in needles) for a in args.values()):
            results.append({'call': history[-1], 'arguments': args, 'trace': list(history)})
        for reg in (ARM_REG_R0, ARM_REG_R1, ARM_REG_R2, ARM_REG_R3, ARM_REG_R12):
            registers.pop(reg, None)
    elif instruction.id in (ARM_INS_B, ARM_INS_BX, ARM_INS_CBZ, ARM_INS_CBNZ, ARM_INS_TBB, ARM_INS_TBH) or (
            instruction.mnemonic.startswith('pop') and 'pc' in instruction.op_str):
        registers.clear()

output = {'kind': 'LINEAR_REFERENCE_CANDIDATES_NOT_CONTROL_FLOW_PROOF',
          'source': str(SOURCE), 'source_sha256': source_sha,
          'base': hex(BASE), 'header_bytes': 512, 'calls': results}
(ROOT / 'evidence/string-reference-candidates.json').write_text(json.dumps(output, indent=2) + '\n')
for result in results:
    print(result['call'], {k: a['string'] for k, a in result['arguments'].items() if a['string']})
print(len(results), 'candidate calls; no runtime claim')
