#!/usr/bin/env python3
"""Offline bounded Thumb inspection of previously verified public LK. No device I/O.
Adapted from boot-access-audit/scripts/{disassemble_lk_authorization,trace_lk_strings}.py.
Linear annotations are candidates, not a control-flow proof; literal pools can decode as code.
"""
from pathlib import Path
import struct,hashlib,json
from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB
from capstone.arm import *
root=Path(__file__).resolve().parents[1]
source=root.parent/'2026-11-05-asus-boot-access-audit/sources/firmware/lk.bin'
data=source.read_bytes(); sha=hashlib.sha256(data).hexdigest()
assert sha=='c5b5017ee3efdf018d9b6be7db978f29365c30e60a3fb9173660fda699f7b765'
base=0x41e00000
regions=[(0x41e03d4c,0x41e04084),(0x41e042bc,0x41e04470),(0x41e04564,0x41e04770),(0x41e04980,0x41e04adc),(0x41e1a908,0x41e1a960),(0x41e1de3c,0x41e1e0e4),(0x41e1e150,0x41e1e25e),(0x41e392dc,0x41e39380),(0x41e39410,0x41e39650),(0x41e39650,0x41e3985a),(0x41e398cc,0x41e39b30),(0x41e3a9d0,0x41e3aae4)]
md=Cs(CS_ARCH_ARM,CS_MODE_THUMB);md.detail=True;md.skipdata=True
lines=[]
def read32(addr):
 off=addr-base+512
 return struct.unpack_from('<I',data,off)[0] if 512<=off<=len(data)-4 else None
def string(addr):
 off=addr-base+512
 if not 512<=off<len(data):return None
 s=data[off:off+200].split(b'\0')[0]
 return repr(s.decode()) if len(s)>3 and all(32<=c<127 or c in [10,13] for c in s) else None
for start,end in regions:
 regs={};lines.append(f'REGION {start:08x}-{end:08x}')
 instructions=list(md.disasm(data[start-base+512:end-base+512],start))
 branch_ids=[ARM_INS_B,ARM_INS_CBZ,ARM_INS_CBNZ]
 targets={i.operands[-1].imm for i in instructions if i.id in branch_ids and i.operands[-1].type==ARM_OP_IMM}
 for ins in instructions:
  if ins.address in targets: regs.clear()
  pc=ins.address+4; ops=ins.operands if ins.id else []; note='';v=None;written=None
  def val(op):
   if op.type==ARM_OP_IMM:return op.imm
   if op.type==ARM_OP_REG:return pc if op.reg==ARM_REG_PC else regs.get(op.reg)
  if ins.id==ARM_INS_LDR and len(ops)>1 and ops[1].type==ARM_OP_MEM:
   mem=ops[1].mem; a=(pc&~3) if mem.base==ARM_REG_PC else regs.get(mem.base); idx=regs.get(mem.index) if mem.index else 0
   if a is not None and idx is not None:
    address=(a+idx+mem.disp)&0xffffffff;v=read32(address);note+=f' ; read [{address:08x}]='+('unknown' if v is None else f'{v:08x}')
   written=ops[0].reg
  elif ins.id in [ARM_INS_MOV,ARM_INS_MOVW] and len(ops)>1:
   written=ops[0].reg;v=val(ops[1])
  elif ins.id==ARM_INS_MOVT:
   written=ops[0].reg;old=regs.get(written)
   if old is not None:v=(old&65535)|(ops[1].imm<<16)
  elif ins.id in [ARM_INS_ADD,ARM_INS_SUB] and len(ops)>=2:
   written=ops[0].reg
   x,y=(val(ops[1]),val(ops[2])) if len(ops)>=3 else (regs.get(written),val(ops[1]))
   if x is not None and y is not None:v=(x+y if ins.id==ARM_INS_ADD else x-y)&0xffffffff
  if ins.id:
   for changed in ins.regs_access()[1]:
    if changed!=written: regs.pop(changed,None)
  if written is not None:
   regs.pop(written,None)
   if v is not None:
    regs[written]=v;s=string(v);note+=f' ; {ins.reg_name(written)}={v:08x}'+(' '+s if s else '')
  lines.append(f'{ins.address:08x} {ins.bytes.hex():10} {ins.mnemonic:10} {ins.op_str}{note}')
  if ins.id in branch_ids or ins.id in [ARM_INS_TBB,ARM_INS_TBH]: regs.clear()
  if ins.mnemonic.startswith('pop') and 'pc' in ins.op_str or ins.id==ARM_INS_BX:
   regs.clear()
  if ins.id in [ARM_INS_BL,ARM_INS_BLX]:
   for r in [ARM_REG_R0,ARM_REG_R1,ARM_REG_R2,ARM_REG_R3,ARM_REG_R12]:regs.pop(r,None)
(root/'evidence/acceptance-disassembly.txt').write_text('\n'.join(lines)+'\n')
(root/'evidence/analysis-manifest.json').write_text(json.dumps({'source':str(source),'sha256':sha,'base':hex(base),'file_header_bytes':512,'regions':[[hex(a),hex(b)] for a,b in regions]},indent=2)+'\n')
print(f'{len(lines)} bounded lines; source SHA256 {sha}')
