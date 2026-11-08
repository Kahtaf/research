#!/usr/bin/env python3
"""Find candidate Thumb PC-relative references in the matching public LK image.
Static linear decoding only; candidates require inspection before semantic claims.
"""
from pathlib import Path
import argparse,struct,json,collections
from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB
from capstone.arm import *
root=Path(__file__).resolve().parents[1];data=(root/'sources/firmware/lk.bin').read_bytes()
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--authorization',action='store_true',help='Trace security/image authorization string candidates instead of command registrations')
options=parser.parse_args()
needles=['fastboot','oem emmc','getvar:','locked state','INVALID FASTBOOT','unlock','decrypted asus key']
if options.authorization:
 needles=['seccfg','SECCFG','SEC_CFG','SEC_UNLOCK','SEC_POLICY','boot_chk_','sec_boot','verify','signature','lock state','unlock','asus key','image auth']
base=0x41e00000;md=Cs(CS_ARCH_ARM,CS_MODE_THUMB);md.detail=True;md.skipdata=True
regs={};history=collections.deque(maxlen=10);results=[]
def read32(addr):
 off=addr-base+512
 return struct.unpack_from('<I',data,off)[0] if 512<=off<=len(data)-4 else None
def val(op,pc):
 if op.type==ARM_OP_IMM:return op.imm
 if op.type==ARM_OP_REG:return pc if op.reg==ARM_REG_PC else regs.get(op.reg)
 return None
def string(addr):
 if addr is None:return None
 off=addr-base+512
 if not 512<=off<len(data):return None
 s=data[off:off+160].split(b'\0')[0]
 if len(s)>3 and all(32<=c<127 or c in [10,13] for c in s):return s.decode()
for ins in md.disasm(data[512:0x43000],base):
 line=f'{ins.address:08x} {ins.mnemonic} {ins.op_str}';history.append(line)
 if not ins.id:regs.clear();continue
 rawpc=ins.address+4;pc=rawpc&~3;ops=ins.operands;written=None;value=None
 if ins.id==ARM_INS_LDR and len(ops)>1 and ops[0].type==ARM_OP_REG and ops[1].type==ARM_OP_MEM:
  mem=ops[1].mem;v=pc if mem.base==ARM_REG_PC else regs.get(mem.base)
  index=regs.get(mem.index) if mem.index else 0
  if v is not None and index is not None:value=read32((v+index+mem.disp)&0xffffffff)
  written=ops[0].reg
 elif ins.id in [ARM_INS_MOV,ARM_INS_MOVW] and len(ops)>1 and ops[0].type==ARM_OP_REG:
  written=ops[0].reg;value=val(ops[1],rawpc)
 elif ins.id==ARM_INS_MOVT and ops[0].type==ARM_OP_REG:
  written=ops[0].reg;old=regs.get(written)
  if old is not None:value=(old&0xffff)|(ops[1].imm<<16)
 elif ins.id in [ARM_INS_ADD,ARM_INS_SUB] and len(ops)>=2 and ops[0].type==ARM_OP_REG:
  written=ops[0].reg
  x,y=(val(ops[1],rawpc),val(ops[2],rawpc)) if len(ops)>=3 else (regs.get(written),val(ops[1],rawpc))
  if x is not None and y is not None:value=(x+y if ins.id==ARM_INS_ADD else x-y)&0xffffffff
 elif ins.id==ARM_INS_ADR:
  written=ops[0].reg;value=pc+ops[1].imm
 if written is not None:
  regs.pop(written,None)
  if value is not None:regs[written]=value
 if ins.id in [ARM_INS_BL,ARM_INS_BLX]:
  args={f'r{i}':dict(value=regs.get(ARM_REG_R0+i),string=string(regs.get(ARM_REG_R0+i))) for i in range(4)}
  if (not options.authorization and ins.op_str == '#0x41e1e500') or any(a['string'] and any(x in a['string'] for x in needles) for a in args.values()):
   results.append(dict(call=line,args=args,trace=list(history)))
  for r in [ARM_REG_R0,ARM_REG_R1,ARM_REG_R2,ARM_REG_R3,ARM_REG_R12]:regs.pop(r,None)
 elif ins.mnemonic in ['bx','pop'] and 'pc' in ins.op_str:regs.clear()
name='lk-authorization-call-candidates.json' if options.authorization else 'lk-string-call-candidates.json'
(root/'evidence'/name).write_text(json.dumps(results,indent=2)+'\n')
for r in results:
 print(r['call'], {k:v for k,v in r['args'].items() if v['string']})
print(len(results),'candidate calls; not control-flow-verified')
