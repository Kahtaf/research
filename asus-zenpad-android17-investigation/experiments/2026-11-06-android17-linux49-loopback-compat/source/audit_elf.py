#!/usr/bin/env python3
from pathlib import Path
import struct,json,hashlib
r=Path(__file__).resolve().parents[1];p=r/'inputs/frozen/inputs/root/apex/com.android.tethering/etc/bpf/mainline/netd.o';b=p.read_bytes()
assert b[:6]==b'\x7fELF\x02\x01'
o=struct.unpack_from('<Q',b,40)[0];n,e,si=struct.unpack_from('<HHH',b,58);assert n==64
sh=[struct.unpack_from('<IIQQQQIIQQ',b,o+i*n) for i in range(e)];strings=b[sh[si][4]:sh[si][4]+sh[si][5]]
out=[]
for x in sh:
 name=strings[x[0]:].split(b'\0')[0].decode()
 if x[2]&4:
  data=b[x[4]:x[4]+x[5]];calls=[]
  for off in range(0,len(data),8):
   op,regs,ofs,imm=struct.unpack_from('<BBhi',data,off)
   if op==0x85:calls.append({'offset':off,'src_reg':regs>>4,'id_or_relative':imm})
  out.append({'section':name,'bytes':len(data),'helper_ids':sorted({a['id_or_relative'] for a in calls if a['src_reg']==0}),'bpf_to_bpf_calls':sum(a['src_reg']==1 for a in calls)})
(r/'evidence/original-elf-calls.json').write_text(json.dumps({'path':str(p.relative_to(r)),'sha256':hashlib.sha256(b).hexdigest(),'sections':out,'boundary':'Direct call scan per ELF code section, not relocation-linked call graph or verifier execution.'},indent=2)+'\n')
for s in out:
 if 'egress' in s['section'] or 'inet_create' in s['section'] or s['section']=='.text':print(json.dumps(s))
