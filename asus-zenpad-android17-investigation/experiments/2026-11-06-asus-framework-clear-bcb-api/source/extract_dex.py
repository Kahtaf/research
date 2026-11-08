from pathlib import Path
import mmap,re,struct,hashlib,zlib,json
S=Path(__file__).resolve().parents[1];out=[]
for name in ['framework__arm64__boot-framework.oat','framework__oat__arm64__services.odex']:
 with (S/'inputs'/name).open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as b:
  oat=[m.start() for m in re.finditer(b'oat\n',b)];print(name,'oat headers',[(x,bytes(b[x:x+8])) for x in oat[:3]])
  count=0
  for m in re.finditer(rb'dex\n0[0-9]{2}\x00',b):
   pos=m.start()
   if pos+112>len(b):continue
   size,header,endian=struct.unpack_from('<III',b,pos+32)
   if header!=112 or endian!=0x12345678 or not 112<=size<=64*1024*1024 or pos+size>len(b):continue
   count+=1;raw=bytes(b[pos:pos+size]);dst=f'{name}.dex{count}';(S/'inputs'/dst).write_bytes(raw)
   out.append(dict(file='inputs/'+dst,container='inputs/'+name,container_sha256=hashlib.sha256(b).hexdigest(),container_offset=pos,bytes=size,sha256=hashlib.sha256(raw).hexdigest(),dex_magic=raw[:8].decode(),sha1_matches=hashlib.sha1(raw[32:]).digest()==raw[12:32],adler32_matches=zlib.adler32(raw[12:])==struct.unpack_from('<I',raw,8)[0]))
  assert count
(S/'evidence/dex-extraction.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
