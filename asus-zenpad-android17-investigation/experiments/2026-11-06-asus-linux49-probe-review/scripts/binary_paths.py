from pathlib import Path
import struct,json,hashlib
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_ARM
from capstone.arm64 import ARM64_OP_IMM, ARM64_OP_REG
R=Path(__file__).resolve().parents[1];md=Cs(CS_ARCH_ARM64,CS_MODE_ARM);md.detail=True;md.skipdata=True
out=[]
for name,needles in [('sbin/adbd',['sys.usb.ffs.ready','/dev/usb-ffs/adb/ep0','/dev/usb-ffs/adb/ep1','/dev/usb-ffs/adb/ep2','ro.secure','ro.debuggable','ro.adb.secure','/adb_keys','/system/bin/sh']),('init',['/init.rc','/sys/fs/selinux/enforce'])]:
 b=(R/'source/ramdisk'/name).read_bytes();po=struct.unpack_from('<Q',b,32)[0];sz,count=struct.unpack_from('<HH',b,54);segs=[struct.unpack_from('<II6Q',b,po+i*sz) for i in range(count)];targets={}
 for needle in needles:
  pos=0
  while True:
   pos=b.find(needle.encode()+b'\0',pos)
   if pos<0:break
   for typ,flags,off,va,pa,fs,ms,al in segs:
    if typ==1 and off<=pos<off+fs:targets[va+pos-off]=needle
   pos+=1
 refs=[];ins=[]
 for typ,flags,off,va,pa,fs,ms,al in segs:
  if typ==1 and flags&1:ins+=list(md.disasm(b[off:off+fs],va))
 for i,q in enumerate(ins):
  if q.mnemonic!='add' or len(q.operands)!=3 or q.operands[2].type!=ARM64_OP_IMM:continue
  src=q.operands[1].reg
  for prev in reversed(ins[max(0,i-7):i]):
   if prev.mnemonic=='adrp' and prev.operands[0].reg==src:
    addr=prev.operands[1].imm+q.operands[2].imm
    if addr in targets:
     context=[f'{v.address:016x} {v.mnemonic} {v.op_str}' for v in ins[max(0,i-24):i+34]]
     refs.append({'string':targets[addr],'string_address':hex(addr),'xref':hex(q.address),'instructions':context})
    break
 out.append({'binary':name,'sha256':hashlib.sha256(b).hexdigest(),'targets':{hex(k):v for k,v in targets.items()},'references':refs})
(R/'evidence/binary-string-paths.json').write_text(json.dumps(out,indent=2)+'\n')
for f in out:
 print(f['binary'],f['targets']);print([(r['string'],r['xref']) for r in f['references']])
