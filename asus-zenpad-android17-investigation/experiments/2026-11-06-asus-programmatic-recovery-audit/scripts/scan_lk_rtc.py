from pathlib import Path
import collections,json,struct,hashlib
from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB
from capstone.arm import *
root=Path(__file__).resolve().parents[1]
source=root.parent/'2026-11-05-asus-boot-access-audit/sources/firmware/lk.bin'
data=source.read_bytes();assert hashlib.sha256(data).hexdigest()=='c5b5017ee3efdf018d9b6be7db978f29365c30e60a3fb9173660fda699f7b765'
base=0x41e00000;md=Cs(CS_ARCH_ARM,CS_MODE_THUMB);md.detail=True;md.skipdata=True
instructions=list(md.disasm(data[512:0x43000],base));matches=[]
for n,i in enumerate(instructions):
 if not i.id:continue
 hit=False
 for o in i.operands:
  if o.type==ARM_OP_IMM and o.imm==0x802c:hit=True
 if i.id==ARM_INS_LDR and len(i.operands)>1 and i.operands[1].type==ARM_OP_MEM and i.operands[1].mem.base==ARM_REG_PC:
  loc=((i.address+4)&~3)+i.operands[1].mem.disp-base+512
  if 512<=loc<=len(data)-4 and struct.unpack_from('<I',data,loc)[0]==0x802c:hit=True
 if hit:
  lines=[f'{x.address:08x} {x.bytes.hex():10} {x.mnemonic:10} {x.op_str}' for x in instructions[max(0,n-12):n+22]]
  matches.append(dict(address=hex(i.address),lines=lines))
(root/'evidence/lk-pdn1-candidates.json').write_text(json.dumps({'scope':'literal-reference candidates only','source_sha256':hashlib.sha256(data).hexdigest(),'matches':matches},indent=2)+'\n')
for m in matches:print('\n'.join(m['lines'])+'\n')
print(len(matches),'RTC_PDN1 candidates')
