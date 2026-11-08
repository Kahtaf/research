#!/usr/bin/env python3
import gzip,hashlib,json,struct,sys
from pathlib import Path
out=Path('/srv/android/lineage24/out/target/product/p00a')
data=(out/'boot.img').read_bytes();assert data[:8]==b'ANDROID!'
k,_,r,_,_,_,_,page=struct.unpack_from('<8I',data,8);start=page+((k+page-1)//page)*page
payload=data[start:start+r];assert payload[:2]==b'\x1f\x8b'
archive=gzip.decompress(payload);pos=0;files={};entries=[]
while True:
 header=archive[pos:pos+110];assert header[:6] in [b'070701',b'070702']
 fields=[int(header[6+i*8:14+i*8],16) for i in range(13)];size=fields[6];namesize=fields[11]
 pos+=110;name=archive[pos:pos+namesize-1].decode();pos=(pos+namesize+3)&~3
 contents=archive[pos:pos+size];pos=(pos+size+3)&~3
 if name=='TRAILER!!!':break
 name=name.removeprefix('./');files[name]=contents
 entries.append(dict(path=name,mode=oct(fields[1]),bytes=size,sha256=hashlib.sha256(contents).hexdigest()))
assert files['fstab.mt8163']==(out/'ramdisk/fstab.mt8163').read_bytes()
assert b'formattable' not in files['fstab.mt8163']
assert files['init']==(out/'ramdisk/init').read_bytes()
elf=files['init'];assert elf[:5]==b'\x7fELF\x02';assert struct.unpack_from('<H',elf,18)[0]==183
phoff=struct.unpack_from('<Q',elf,32)[0];phentsize,phnum=struct.unpack_from('<HH',elf,54)
assert not any(struct.unpack_from('<I',elf,phoff+i*phentsize)[0]==3 for i in range(phnum))
Path(sys.argv[1]).write_text(json.dumps(dict(boot_sha256=hashlib.sha256(data).hexdigest(),ramdisk_compression='gzip',init_elf_arch='AArch64',init_static=True,fstab=files['fstab.mt8163'].decode(),entries=entries,automatic_formatting=False,physical_boot_verified=False),indent=2)+'\n')
print('Built boot ramdisk has static ARM64 init and exact gated fstab without autoformat.')
