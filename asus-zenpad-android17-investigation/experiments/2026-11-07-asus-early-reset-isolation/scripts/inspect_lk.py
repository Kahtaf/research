from pathlib import Path
import struct as S,hashlib,json
from capstone import Cs,CS_ARCH_ARM,CS_MODE_ARM
from capstone.arm import ARM_INS_LDR,ARM_OP_MEM,ARM_REG_PC
R=Path(__file__).resolve().parents[1];W=R.parent
p=W/'2026-11-05-asus-boot-access-audit/sources/firmware/lk.bin';d=p.read_bytes();assert hashlib.sha256(d).hexdigest()=='c5b5017ee3efdf018d9b6be7db978f29365c30e60a3fb9173660fda699f7b765'
base=0x41e00000;offset=lambda a:a-base+512
strings={}
for term in [b'wdt_by_pass_pwk',b'watchdog',b'RAM_CONSOLE',b'lk boot reason',b'lk finished',b'[LK]jump to K64']:
 pos=d.find(term);print(term,hex(pos),hex(base+pos-512));strings[base+pos-512]=term.decode()
md=Cs(CS_ARCH_ARM,CS_MODE_ARM);md.detail=True;md.skipdata=True
refs=[]
for ins in md.disasm(d[512:300000],base):
 if ins.id==ARM_INS_LDR and len(ins.operands)>1 and ins.operands[1].type==ARM_OP_MEM and ins.operands[1].mem.base==ARM_REG_PC:
  a=(ins.address+8)+ins.operands[1].mem.disp;o=offset(a)
  if 512<=o<=len(d)-4:
   v=S.unpack_from('<I',d,o)[0]
   if v in strings or v in [0x10007000,0x43474244,0x44400000]:refs.append((ins.address,v))
print('REFS',[(hex(a),hex(v),strings.get(v)) for a,v in refs])
regions=[]
for a,v in refs:
 if v in [0x10007000,0x43474244,0x44400000] or v in strings:regions.append((max(base,a-128),a+320))
lines=[]
for a,b in regions:
 lines.append(f'REGION {a:x}-{b:x} (linear decode; literal/data and reachability need manual review)')
 for ins in md.disasm(d[offset(a):offset(b)],a):
  note=''
  if ins.id==ARM_INS_LDR and len(ins.operands)>1 and ins.operands[1].type==ARM_OP_MEM and ins.operands[1].mem.base==ARM_REG_PC:
   x=(ins.address+8)+ins.operands[1].mem.disp;o=offset(x)
   if 512<=o<=len(d)-4:
    v=S.unpack_from('<I',d,o)[0];note=f' ; [{x:x}]={v:x} '+strings.get(v,'')
  lines.append(f'{ins.address:08x} {ins.bytes.hex()} {ins.mnemonic} {ins.op_str}{note}')
(R/'evidence/lk-watchdog-header.disasm').write_text('\n'.join(lines)+'\n')
