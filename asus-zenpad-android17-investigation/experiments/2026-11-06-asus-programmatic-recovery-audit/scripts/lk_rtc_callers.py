from pathlib import Path
import json
from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB
from capstone.arm import *
root=Path(__file__).resolve().parents[1]
data=(root.parent/'2026-11-05-asus-boot-access-audit/sources/firmware/lk.bin').read_bytes();base=0x41e00000
md=Cs(CS_ARCH_ARM,CS_MODE_THUMB);md.detail=True;md.skipdata=True
ops=list(md.disasm(data[512:0x43000],base));targets={0x41e08320,0x41e08378,0x41e07f8c,0x41e06acc,0x41e06adc,0x41e07f1c}
rows=[]
for n,i in enumerate(ops):
 if i.id not in (ARM_INS_BL,ARM_INS_BLX) or not i.operands or i.operands[0].type!=ARM_OP_IMM or i.operands[0].imm not in targets:continue
 target=i.operands[0].imm
 if target in (0x41e06acc,0x41e06adc,0x41e07f1c):continue
 lines=[f'{x.address:08x} {x.bytes.hex():10} {x.mnemonic:10} {x.op_str}' for x in ops[max(0,n-16):n+18]]
 rows.append(dict(call=hex(i.address),target=hex(target),lines=lines))
(root/'evidence/lk-rtc-callers.json').write_text(json.dumps({'scope':'candidate call sites; inspect bounded control flow before claims','callers':rows},indent=2)+'\n')
for row in rows:print('\n'.join(row['lines'])+'\n')
print(len(rows),'call sites')
