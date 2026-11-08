#!/usr/bin/env python3
"""Decode exact e9 kallsyms and retain only relevant timer/CPU slices."""
from pathlib import Path
import struct as S, zlib, hashlib, json, re
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
R=Path(__file__).resolve().parents[1]
b=zlib.decompressobj(31).decompress((R.parent/'2026-11-06-asus-bmc156-full-kernel/artifacts/Image.gz-dtb').read_bytes())
assert hashlib.sha256(b).hexdigest()=='43ee0529e371575bfaddb9de392b77a2279cb44bc60649fcd8d9a88b6e613b09'
align=lambda n:(n+255)&~255
base=S.unpack_from('<Q',b,0xc2cd00)[0]
n=S.unpack_from('<Q',b,0xc2ce00)[0]
assert base==0xffffff8008080000 and n==42362
offstart=0xc2cd00-align(n*4)
offsets=S.unpack_from('<%dI'%n,b,offstart)
assert offsets[0]==0x1000 and list(offsets)==sorted(offsets)
names=p=0xc2cf00; encoded=[];markers=[]
for i in range(n):
 if i%256==0:markers.append(p-names)
 size=b[p];assert 0<size<128
 encoded.append(b[p+1:p+1+size]);p+=size+1
mo=align(p)
assert list(S.unpack_from('<%dQ'%len(markers),b,mo))==markers
to=p=align(mo+8*len(markers));tokens=[];idx=[]
for i in range(256):
 idx.append(p-to);end=b.index(0,p);tokens.append(b[p:end].decode());p=end+1
assert list(S.unpack_from('<256H',b,align(p)))==idx
syms={}
for off,enc in zip(offsets,encoded):
 text=''.join(tokens[v] for v in enc)
 assert re.fullmatch(r'[a-zA-Z?][a-zA-Z0-9_.$@]+',text)
 syms[text[1:]]=base+off
rev={v:k for k,v in syms.items()}
want=['mtk_timer_init','cpu_read_ops','mt_psci_cpu_boot','time_init','mtk_infrasys_init','mtk_topckgen_init','arch_timer_of_init']
md=Cs(CS_ARCH_ARM64,CS_MODE_ARM);lines=[];facts={}
for name in want:
 assert name in syms,name
 addr=syms[name];off=addr-base
 end=min(v for v in syms.values() if v>addr);size=end-addr
 facts[name]=dict(address=hex(addr),offset=hex(off),bytes=size,sha256=hashlib.sha256(b[off:off+size]).hexdigest())
 lines.append('FUNCTION %s %#x bytes=%d'%(name,addr,size))
 for ins in md.disasm(b[off:off+size],addr):
  note=''
  if ins.mnemonic in ('bl','b') and ins.op_str.startswith('#'):
   note=' ; '+rev.get(int(ins.op_str[1:],16),'?')
  lines.append('%016x %s %s %s%s'%(ins.address,ins.bytes.hex(),ins.mnemonic,ins.op_str,note))
 lines.append('')
(R/'evidence/e9-focused.disasm').write_text('\n'.join(lines)+'\n')
(R/'evidence/e9-symbols.json').write_text(json.dumps(dict(symbol_count=n,all_names_markers_token_indices_valid=True,selected=facts),indent=2)+'\n')
print(json.dumps(facts,indent=2))
