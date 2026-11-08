#!/usr/bin/env python3
"""Discover RTC/recovery literal references in the exact saved preloader.
Linear ARM/Thumb candidates only; this is not a control-flow or runtime proof.
No target operations or image modifications exist in this script.
"""
from pathlib import Path
import collections
import hashlib
import json
import struct
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM, CS_MODE_THUMB
from capstone.arm import *
ROOT=Path(__file__).resolve().parents[1]
OLD=ROOT.parent/'2026-11-05-asus-boot-access-audit'
path=OLD/'sources/firmware/preloader_asus8163_ew_380.bin'
data=path.read_bytes()
assert data[:4]==b'MMM\x01' and data[8:20].rstrip(b'\0')==b'FILE_INFO'
base,size,maximum,content,signature,jump,attributes=struct.unpack_from('<7I',data,28)
assert size==len(data) and base==0x200d00 and content==jump==0x300 and signature==0x124
matches={}
for label in ('initial','verify'):
 for area in ('boot1','boot2'):
  f=OLD/'artifacts/device-backup'/label/(area+'.bin')
  with f.open('rb') as source:
   source.seek(2048); actual=source.read(len(data))
  assert actual==data
  matches[label+'/'+area]=True

def word(addr):
 off=addr-base
 return struct.unpack_from('<I',data,off)[0] if content<=off<=size-signature-4 else None

def string(addr):
 if addr is None:return None
 off=addr-base
 if not content<=off<size-signature:return None
 b=data[off:off+200].split(b'\0')[0]
 return b.decode('ascii') if len(b)>3 and all(32<=c<127 or c in (10,13) for c in b) else None

found=[]
for mode,name,bias in [(CS_MODE_ARM,'arm',8),(CS_MODE_THUMB,'thumb',4)]:
 md=Cs(CS_ARCH_ARM,mode);md.detail=True;md.skipdata=True
 regs={};history=collections.deque(maxlen=12)
 for ins in md.disasm(data[content:0x22b00],base+content):
  history.append(f'{ins.address:08x} {ins.bytes.hex():10} {ins.mnemonic} {ins.op_str}')
  if not ins.id:regs.clear();continue
  pc=ins.address+bias;ops=ins.operands;changed=None;value=None
  def val(op):
   if op.type==ARM_OP_IMM:return op.imm
   if op.type==ARM_OP_REG:return pc if op.reg==ARM_REG_PC else regs.get(op.reg)
  if ins.id==ARM_INS_LDR and len(ops)>1 and ops[1].type==ARM_OP_MEM:
   mem=ops[1].mem;a=(pc&~3) if mem.base==ARM_REG_PC else regs.get(mem.base);idx=regs.get(mem.index) if mem.index else 0
   if a is not None and idx is not None:value=word((a+idx+mem.disp)&0xffffffff)
   changed=ops[0].reg
  elif ins.id in (ARM_INS_MOV,ARM_INS_MOVW) and len(ops)>1:
   changed=ops[0].reg;value=val(ops[1])
  elif ins.id==ARM_INS_MOVT:
   changed=ops[0].reg;old=regs.get(changed)
   if old is not None:value=(old&65535)|(ops[1].imm<<16)
  elif ins.id in (ARM_INS_ADD,ARM_INS_SUB) and len(ops)>=2:
   changed=ops[0].reg
   x,y=(val(ops[1]),val(ops[2])) if len(ops)>=3 else (regs.get(changed),val(ops[1]))
   if x is not None and y is not None:value=(x+y if ins.id==ARM_INS_ADD else x-y)&0xffffffff
  for r in ins.regs_access()[1]:
   if r!=changed:regs.pop(r,None)
  if changed is not None:
   regs.pop(changed,None)
   if value is not None:regs[changed]=value
  if ins.id in (ARM_INS_BL,ARM_INS_BLX):
   args={f'r{i}':dict(value=regs.get(ARM_REG_R0+i),string=string(regs.get(ARM_REG_R0+i))) for i in range(4)}
   if any(x['string'] and any(n in x['string'].lower() for n in ('rtc','recovery','pdn1')) for x in args.values()):
    found.append(dict(mode=name,address=hex(ins.address),call=ins.op_str,args=args,trace=list(history)))
   for r in (ARM_REG_R0,ARM_REG_R1,ARM_REG_R2,ARM_REG_R3,ARM_REG_R12):regs.pop(r,None)
  if ins.id in (ARM_INS_B,ARM_INS_BX,ARM_INS_CBZ,ARM_INS_CBNZ) or (ins.id==ARM_INS_POP and any(o.type==ARM_OP_REG and o.reg==ARM_REG_PC for o in ops)):regs.clear()
result=dict(scope='linear candidate discovery only; no one-shot/runtime claim',source=str(path),sha256=hashlib.sha256(data).hexdigest(),load_base=hex(base),content_offset=content,saved_boot_area_matches=matches,candidates=found,device_contacted=False)
(ROOT/'evidence/preloader-rtc-candidates.json').write_text(json.dumps(result,indent=2)+'\n')
for row in found:
 print(row['mode'],row['address'],row['call'],{k:v['string'] for k,v in row['args'].items() if v['string']})
print(len(found),'candidates; four saved boot-area copies match exact preloader')
