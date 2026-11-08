from analyze import *
from capstone.arm import *
b=Binary(ROOT/'inputs/lib_libcam.halsensor.so');cs=Cs(CS_ARCH_ARM,CS_MODE_THUMB);cs.detail=True
s=b.e.get_section_by_name('.text');data=s.data();a=s['sh_addr'];out=[]
for off in range(0,len(data)-20,2):
 seq=list(cs.disasm(data[off:off+24],a+off));
 if not seq:continue
 i=seq[0]
 if not i.mnemonic.startswith('ldr') or '[pc,' not in i.op_str:continue
 m=re.search(r'\[pc, #(-?0x[0-9a-f]+|-?[0-9]+)\]',i.op_str)
 if not m:continue
 targetreg=i.op_str.split(',')[0];v=int.from_bytes(b.read(((i.address+4)&~3)+int(m[1],0),4),'little')
 for j in seq[1:]:
  if j.op_str==targetreg+', pc' and j.mnemonic=='add':
   target=(v+j.address+4)&0xffffffff
   if target in b.rel and b.rel[target][0] in ['gSensorMetadata','sensorStaticInfo']:
    out.append({'load':hex(i.address),'add':hex(j.address),'got':hex(target),'symbol':b.rel[target][0]})
   break
  if j.op_str.startswith(targetreg+',') and not j.mnemonic.startswith(('cmp','str')):break
print(json.dumps(out,indent=2));(ROOT/'evidence/halsensor-global-references.json').write_text(json.dumps(out,indent=2))
