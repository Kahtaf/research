from pathlib import Path
import sys,struct,json,hashlib
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'2026-11-06-asus-stock-userdata-recovery/source'))
from elfaudit import ELF
S=Path(__file__).resolve().parents[1];e=ELF(ROOT/'2026-11-06-asus-pending-recovery-request/source/uncrypt')
(S/'evidence/uncrypt-all.txt').write_text(e.listing(e.sections['.text'][3],e.sections['.text'][3]+e.sections['.text'][5]))
s=e.sections['.dynsym'];st=e.sections['.dynstr'];strings=e.data[st[4]:st[4]+st[5]];syms=[]
for off in range(s[4],s[4]+s[5],s[9]):
 name,info,other,shndx,value,size=struct.unpack_from('<IBBHQQ',e.data,off);syms.append(dict(name=strings[name:].split(b'\0')[0].decode(),value=hex(value),size=size))
r=e.sections['.rela.plt'];plt={}
for idx,off in enumerate(range(r[4],r[4]+r[5],r[9])):
 target,info,addend=struct.unpack_from('<QQq',e.data,off);plt[hex(e.sections['.plt'][3]+32+idx*16)]=syms[info>>32]['name']
(S/'evidence/uncrypt-plt.json').write_text(json.dumps(plt,indent=2))
(S/'evidence/uncrypt-symbols.json').write_text(json.dumps(syms,indent=2))
refs=e.stringrefs(['--clear-bcb','--setup-bcb','/misc','emmc','/fstab.','ro.hardware','uncrypt','/cache/recovery/command'])
(S/'evidence/uncrypt-refs.json').write_text(json.dumps(refs,indent=2));print(json.dumps(refs,indent=2));print(json.dumps(plt,indent=2))
print(e.sections)
regs={};lines=[]
for i in e.instructions():
 note='';ops=i.operands;value=None
 if i.mnemonic in ('adrp','adr'):value=ops[1].imm
 elif i.mnemonic=='add' and len(ops)==3 and ops[1].type==1 and ops[2].type==2 and ops[1].reg in regs:value=regs[ops[1].reg]+ops[2].imm
 for r in i.regs_access()[1]:regs.pop(r,None)
 if value is not None:
  regs[ops[0].reg]=value
  if i.mnemonic!='adrp':
   try:
    s=e.string(value)
    if s and all(c.isprintable() or c in '\n\t\r' for c in s):note=repr(s)
   except ValueError:pass
 if i.mnemonic in ('bl','b') and ops[0].type==2:note=plt.get(hex(ops[0].imm),'')
 lines.append(f'{i.address:08x} {i.bytes.hex():8s} {i.mnemonic:8s} {i.op_str:32s} {note}')
 if i.mnemonic in ('ret','b','bl','blr','br'):regs={}
(S/'evidence/uncrypt-annotated.txt').write_text('\n'.join(lines)+'\n')
