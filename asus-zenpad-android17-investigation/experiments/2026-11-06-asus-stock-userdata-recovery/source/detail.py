from pathlib import Path
from elfaudit import ELF
import struct,json
S=Path(__file__).resolve().parents[1];e=ELF(S/'inputs/recovery__sbin_recovery')
for name,a,b in [('oem-wipe',0x40d7ec,0x40d990),('erase-volume',0x404088,0x4044bc),('oem-bookkeeping',0x40db7c,0x40e128),('device-ui',0x400300,0x401330),('wipe-callers',0x406300,0x4064b0),('finish-recovery',0x403e9c,0x404088),('format-ext4',0x40805c,0x408244)]:
 (S/f'evidence/{name}.txt').write_text(e.listing(a,b))
for a in [0x51f8cb,0x51fd2c,0x51fab7,0x51ee82,0x51eeac,0x51eeb2]:print(hex(a),repr(e.string(a)))
# Resolve all adjacent ADRP/ADD string literals in early OEM code, retaining listing for manual interpretation.
refs=[];ins=list(e.instructions(0x4001c0,0x40e500));regs={}
for i in ins:
 op=i.operands
 if i.mnemonic=='adrp':regs[op[0].reg]=op[1].imm
 elif i.mnemonic=='add' and len(op)==3 and op[1].type==1 and op[2].type==2 and op[1].reg in regs:
  a=regs[op[1].reg]+op[2].imm
  try:
   s=e.string(a)
   if s and all(c.isprintable() or c in '\n\t\r' for c in s):refs.append({'pc':hex(i.address),'va':hex(a),'text':s})
  except (ValueError,IndexError):pass
 elif i.mnemonic in ['ret','bl','blr','b']:regs={}
(S/'evidence/early-literals.json').write_text(json.dumps(refs,indent=2)+'\n')
for i in e.instructions():
 if i.mnemonic=='bl' and i.op_str=='#0x40d7ec':print('wipe caller',hex(i.address))
for pos in range(0,len(e.data)-8,8):
 val=struct.unpack_from('<Q',e.data,pos)[0]
 if val==0x40d988:print('default hook ptr offset',hex(pos))
