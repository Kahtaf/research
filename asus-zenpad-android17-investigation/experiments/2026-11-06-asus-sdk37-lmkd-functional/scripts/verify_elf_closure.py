from pathlib import Path
import struct,json,hashlib
P=Path(__file__).resolve().parent.parent;I=P/'artifacts/frozen/inputs/native-r3';manifest=json.loads((I/'manifest.json').read_text());out={}
for item in manifest:
 f=I/item['name'];b=f.read_bytes();assert hashlib.sha256(b).hexdigest()==item['sha256'];h=struct.unpack_from('<16sHHIQQQIHHHHHH',b);assert h[0][:6]==b'\x7fELF\x02\x01' and h[2]==183
 ph=[struct.unpack_from('<IIQQQQQQ',b,h[5]+n*h[9]) for n in range(h[10])];dynamic=next((p for p in ph if p[0]==2),None);tags=[]
 if dynamic:
  for offset in range(dynamic[2],dynamic[2]+dynamic[5],16):
   tag,val=struct.unpack_from('<qQ',b,offset)
   if tag==0:break
   tags.append((tag,val))
 straddr=next((val for tag,val in tags if tag==5),0);strbase=next((p[2]+straddr-p[3] for p in ph if p[0]==1 and p[3]<=straddr<p[3]+p[5]),None)
 def name(v):
  assert strbase is not None;start=strbase+v;return b[start:b.index(b'\0',start)].decode()
 out[item['name']]={'bytes':len(b),'sha256':item['sha256'],'elf':'ELF64 little-endian AArch64','needed':[name(v) for t,v in tags if t==1],'soname':next((name(v) for t,v in tags if t==14),None)}
providers={x['soname'] or n:n for n,x in out.items()};missing=[(n,d) for n,x in out.items() for d in x['needed'] if d not in providers];assert not missing,missing
(P/'evidence/elf-runtime-closure.json').write_text(json.dumps({'verified':True,'providers':providers,'files':out,'missing':missing},indent=2));print('verified',len(out),'ELFs,',sum(x['bytes'] for x in out.values()),'bytes; linker provider',providers.get('ld-android.so'))
