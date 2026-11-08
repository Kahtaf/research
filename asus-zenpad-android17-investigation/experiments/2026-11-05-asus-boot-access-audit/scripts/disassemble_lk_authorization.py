#!/usr/bin/env python3
"""Save bounded, annotated Thumb decoding of the exact public ASUS LK.

Literal pools are also decoded linearly; this is evidence for manual control-flow
review, not a decompiler or proof that every displayed instruction is reachable.
No USB or device access is performed.
"""
from pathlib import Path
import hashlib
import struct
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB
from capstone.arm import ARM_INS_LDR, ARM_OP_MEM, ARM_REG_PC

root = Path(__file__).resolve().parents[1]
data = (root / 'sources/firmware/lk.bin').read_bytes()
assert hashlib.sha256(data).hexdigest() == 'c5b5017ee3efdf018d9b6be7db978f29365c30e60a3fb9173660fda699f7b765'
base = 0x41e00000
decoder = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
decoder.detail = True
decoder.skipdata = True
regions = [
    (0x41e39edc, 0x41e3a470),  # seccfg read, crypt wrappers, lock getter/setter
    (0x41e3a798, 0x41e3ab90),  # lock-state/policy selection
    (0x41e39640, 0x41e39940),  # image checks
    (0x41e3f398, 0x41e3f4c0),  # crypto dispatch
]
lines = []
for start, end in regions:
    lines.append(f'REGION {start:08x}-{end:08x}')
    for ins in decoder.disasm(data[start - base + 512:end - base + 512], start):
        note = ''
        if (ins.id == ARM_INS_LDR and len(ins.operands) > 1
                and ins.operands[1].type == ARM_OP_MEM
                and ins.operands[1].mem.base == ARM_REG_PC):
            addr = ((ins.address + 4) & ~3) + ins.operands[1].mem.disp
            offset = addr - base + 512
            if 512 <= offset <= len(data) - 4:
                note = f' ; [{addr:08x}]={struct.unpack_from("<I", data, offset)[0]:08x}'
        lines.append(f'{ins.address:08x} {ins.mnemonic:10} {ins.op_str}{note}')
output = root / 'evidence/lk-seccfg-policy-disassembly.txt'
output.write_text('\n'.join(lines) + '\n')
print(f'{len(lines)} lines saved to {output}')
