from pathlib import Path
import struct
from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB
from capstone.arm import *
root=Path(__file__).resolve().parents[1]
data=(root.parent/'2026-11-05-asus-boot-access-audit/sources/firmware/preloader_asus8163_ew_380.bin').read_bytes()
base=struct.unpack_from('<I',data,28)[0]
md=Cs(CS_ARCH_ARM,CS_MODE_THUMB);md.detail=True
regions=[(0x213940,0x213a30),(0x216b00,0x217160)]
lines=[]
for start,end in regions:
 lines.append(f'REGION {start:08x} {end:08x}')
 for i in md.disasm(data[start-base:end-base],start):
  note=''
  if i.id==ARM_INS_LDR and len(i.operands)>1 and i.operands[1].type==ARM_OP_MEM and i.operands[1].mem.base==ARM_REG_PC:
   p=((i.address+4)&~3)+i.operands[1].mem.disp
   if 0<=p-base<=len(data)-4:note=f' ; literal {struct.unpack_from("<I",data,p-base)[0]:08x}'
  lines.append(f'{i.address:08x} {i.bytes.hex():10} {i.mnemonic:10} {i.op_str}{note}')
(root/'evidence/preloader-rtc-regions.txt').write_text('\n'.join(lines)+'\n')
print('Wrote',len(lines),'bounded disassembly lines; not a control-flow proof')
