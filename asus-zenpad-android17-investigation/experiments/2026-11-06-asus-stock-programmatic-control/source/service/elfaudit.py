"""Offline ELF64/AArch64 readers and bounded disassembly, no execution."""
from pathlib import Path
import struct
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_ARM
from capstone.arm64_const import ARM64_OP_REG,ARM64_OP_IMM
class ELF:
 def __init__(self,path):
  self.path=Path(path);self.data=self.path.read_bytes();b=self.data
  assert b[:6]==b'\x7fELF\x02\x01' and struct.unpack_from('<H',b,18)[0]==183
  self.entry=struct.unpack_from('<Q',b,24)[0]
  off=struct.unpack_from('<Q',b,32)[0];sz,n=struct.unpack_from('<HH',b,54)
  self.ph=[struct.unpack_from('<IIQQQQQQ',b,off+i*sz) for i in range(n)]
  off=struct.unpack_from('<Q',b,40)[0];sz,n,strings=struct.unpack_from('<HHH',b,58)
  self.sh=[struct.unpack_from('<IIQQQQIIQQ',b,off+i*sz) for i in range(n)]
  st=self.sh[strings];names=b[st[4]:st[4]+st[5]]
  self.sections={names[x[0]:].split(b'\0')[0].decode():x for x in self.sh}
  self.md=Cs(CS_ARCH_ARM64,CS_MODE_ARM);self.md.detail=True
 def offset(self,va):
  for t,f,o,v,pa,fs,ms,al in self.ph:
   if t==1 and v<=va<v+fs:return o+va-v
  raise ValueError(hex(va))
 def bytes(self,a,b):return self.data[self.offset(a):self.offset(a)+b-a]
 def string(self,va):return self.data[self.offset(va):].split(b'\0')[0][:200].decode(errors='replace')
 def instructions(self,a=None,b=None):
  if a is None:
   x=self.sections['.text'];a=x[3];b=a+x[5]
  return self.md.disasm(self.bytes(a,b),a)
 def listing(self,a,b):return '\n'.join(f'{i.address:08x} {i.bytes.hex():8s} {i.mnemonic:8s} {i.op_str}' for i in self.instructions(a,b))+'\n'
 def stringrefs(self,terms):
  addresses=set()
  for term in terms:
   start=0
   while True:
    p=self.data.find(term.encode(),start)
    if p<0:break
    for t,f,o,v,pa,fs,ms,al in self.ph:
     if t==1 and o<=p<o+fs:addresses.add(v+p-o)
    start=p+len(term)
  regs={};out=[]
  for i in self.instructions():
   ops=i.operands;value=None
   if i.mnemonic in ('adr','adrp') and len(ops)==2 and ops[1].type==ARM64_OP_IMM:value=ops[1].imm
   elif i.mnemonic=='add' and len(ops)==3 and ops[1].type==ARM64_OP_REG and ops[2].type==ARM64_OP_IMM and ops[1].reg in regs:value=regs[ops[1].reg]+ops[2].imm
   _,writes=i.regs_access()
   for r in writes:regs.pop(r,None)
   if value is not None:
    regs[ops[0].reg]=value
    if value in addresses:out.append(dict(pc=hex(i.address),target=hex(value),string=self.string(value)))
   if i.mnemonic in ('ret','b','bl','blr','br'):regs.clear()
  return out
if __name__=='__main__':
 import argparse,json
 p=argparse.ArgumentParser();p.add_argument('file');p.add_argument('--start',type=lambda x:int(x,16));p.add_argument('--end',type=lambda x:int(x,16));a=p.parse_args();e=ELF(a.file)
 if a.start:print(e.listing(a.start,a.end))
 else:print(json.dumps(e.stringrefs(['sys.powerctl','boot-recovery','reboot','recovery','powerctl','/cache/recovery','/cache/recovery/command']),indent=2))
