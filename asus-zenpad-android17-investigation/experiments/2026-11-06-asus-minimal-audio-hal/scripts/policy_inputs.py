from pathlib import Path
import os,resource,subprocess,json,struct
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
a=Path('/srv/android/lineage24');root=a/'out/soong/.intermediates/system/sepolicy'
for p in root.rglob('*.cil'):
 if p.name in ['plat_sepolicy.cil','vendor_sepolicy.cil','plat_pub_versioned.cil','system_ext_sepolicy.cil','product_sepolicy.cil'] or 'mapping' in p.name or p.name[0].isdigit():print(p,p.stat().st_size)
s=(a/'system/sepolicy/Android.bp').read_text();idx=s.find('name: "precompiled_sepolicy"');print(s[idx-200:idx+2400])
# Decode only referenced public constant string addresses, no record values.
p=Path('/srv/android/asus-hardware-completeness-audit/public-selected/lib64_hw_audio.primary.mt8163.so');data=p.read_bytes();phoff=struct.unpack_from('<Q',data,32)[0];phsize,phnum=struct.unpack_from('<HH',data,54)
for address in [0xcb88b,0xcb8c7,0xcb8dd,0xcb8e2,0xcb8f8,0xcb909,0xcb91a]:
 for i in range(phnum):
  typ,flags,off,va,pa,fs,ms,align=struct.unpack_from('<IIQQQQQQ',data,phoff+i*phsize)
  if typ==1 and va<=address<va+fs:
   pos=off+address-va;end=data.index(b'\0',pos);print('PUBLIC_STRING',hex(address),data[pos:end].decode(errors='replace'))
