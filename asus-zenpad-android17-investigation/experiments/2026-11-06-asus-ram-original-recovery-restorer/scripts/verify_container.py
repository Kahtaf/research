"""Independent parser: no assembly or bootformat imports; actual output bytes."""
from pathlib import Path
import hashlib,json,struct,zlib,collections,sys
R=Path(__file__).resolve().parents[1];A=R/'artifacts';C=A/'candidate'
sha=lambda x:hashlib.sha256(x).hexdigest()
def align(x,n):return (x+n-1)//n*n
def cpio(raw,canonical=True):
 p=0;e={}
 while True:
  assert raw[p:p+6]==b'070701';v=[int(raw[p+6+i*8:p+14+i*8],16) for i in range(13)]
  ino,mode,uid,gid,links,mtime,size,maj,minr,rmaj,rmin,ns,checksum=v
  assert 1<=ns<=4096
  if canonical:assert mtime==maj==minr==rmaj==rmin==checksum==0
  name=raw[p+110:p+110+ns];assert name[-1:]==b'\0';name=name[:-1].decode();p=align(p+110+ns,4)
  data=raw[p:p+size];assert len(data)==size;p=align(p+size,4)
  if name=='TRAILER!!!':
   assert size==0
   if canonical:assert mode==uid==gid==0
   break
  assert name not in e and not name.startswith('/') and '..' not in name.split('/')
  e[name]=(mode,uid,gid,data)
 assert not any(raw[p:]);return e
image=(C/'UNARMED.img').read_bytes();full=(C/'UNARMED.p10.raw').read_bytes()
assert len(full)==16740352 and full==image+bytes(len(full)-len(image))
assert image[:8]==b'ANDROID!'
ks,ka,rs,ra,ss,sa,tags,page=struct.unpack_from('<8I',image,8);assert page==2048 and ss==0
ro=page+align(ks,page);assert len(image)==ro+align(rs,page)
k=image[page:page+ks];r=image[ro:ro+rs]
for part,magic in [(k,b'KERNEL'),(r,b'RECOVERY')]:
 assert part[:4]==bytes.fromhex('88168858') and struct.unpack_from('<I',part,4)[0]==len(part)-512 and part[8:40].split(b'\0')[0]==magic
assert not any(image[page+ks:ro]) and not any(image[ro+rs:])
assert image[576:608]==hashlib.sha1(k+struct.pack('<I',ks)+r+struct.pack('<II',rs,0)).digest()+bytes(12)
assert sha(k)=='b0e5d48bf2889b418dda0fc867f70e42e27a0aeb0a0a3d37539d9a7435430880'
z=zlib.decompressobj(31);raw=z.decompress(r[512:],64*1024*1024);assert z.eof and not z.unconsumed_tail
core=cpio(raw);unused=z.unused_data;consumed=len(r)-512-len(unused);pad=(-consumed)%4
assert not any(unused[:pad]);capsule=unused[pad:];extra=cpio(capsule)
assert set(extra)=={'sbin/p10-restore'} and extra['sbin/p10-restore']==(0o100700,0,0,(A/'p10-restore').read_bytes())
assert capsule==(C/'helper.cpio').read_bytes()
assert r[512:len(r)-len(capsule)]==(A/'core.cpio.gz').read_bytes()
assert core['rescue.manifest'][3]==(A/'unarmed.manifest').read_bytes() and len(core['rescue.manifest'][3])==112
assert core['rescue.manifest'][3][:16]==b'ASUSR002\x02\0\0\0\0\0\0\0'
for name,artifact in [('sepolicy','restore-sepolicy'),('file_contexts.bin','file_contexts.bin'),('sbin/os-rescue','os-rescue'),('system/bin/sh','rescue-proxy')]:assert core[name][3]==(A/artifact).read_bytes()
assert core['sbin/rescue-proxy']==core['system/bin/sh']
assert b'/sbin/p10-restore' in core['init.rc'][3] and b'oneshot' in core['init.rc'][3]
assert not any(n in core for n in ['sbin/recovery','fstab','system/bin/bash'])
elfs={}
for n,x in [('os-rescue',(A/'os-rescue').read_bytes()),('p10-restore',(A/'p10-restore').read_bytes())]:
 assert x[:6]==b'\x7fELF\x02\x01' and struct.unpack_from('<H',x,18)[0]==183
 off=struct.unpack_from('<Q',x,32)[0];size,count=struct.unpack_from('<HH',x,54)
 types=[struct.unpack_from('<I',x,off+i*size)[0] for i in range(count)];assert 2 not in types and 3 not in types
 elfs[n]=dict(sha256=sha(x),bytes=len(x),static_aarch64=True)
assert (A/'p10-restore').read_bytes()==(A/'p10-restore-reproduction').read_bytes()
assert sha((A/'legacy-reproduction').read_bytes())=='30ae9252e575d7c9c837783d60e51016a16bcadb46bd38215d8e49e5bb5d1c53'
# Compare preserved stock components to actual original public recovery.
stock=(A/'original-recovery.payload').read_bytes();sks,srs=struct.unpack_from('<I',stock,8)[0],struct.unpack_from('<I',stock,16)[0]
sro=2048+align(sks,2048);sz=zlib.decompressobj(31);se=cpio(sz.decompress(stock[sro+512:sro+srs]),False)
assert k==stock[2048:2048+sks]
for n in ['init','sbin/adbd','property_contexts','seapp_contexts','service_contexts']:assert core[n]==se[n]
contract=json.loads((C/'session-contract.UNAPPROVED.json').read_text());assert contract['p10_full_sha256']==sha(full) and contract['image_sha256']==sha(image) and not contract['armed'] and not contract['execute_approved']
sys.path.insert(0,str(R/'source'));from file_contexts import extract
rows=extract(core['file_contexts.bin'][3]);assert sum(kind=='-b' and 'rescue_' in ctx for _,kind,ctx in rows)==9
result=dict(passed=True,image_sha256=sha(image),padded_p10_sha256=sha(full),image_bytes=len(image),ramdisk_bytes=rs-512,
 reservation_headroom=0x400000-(rs-512),stock_kernel_unchanged=True,stock_init_adbd_unchanged=True,
 exact_two_member_layout=True,compressed_core_bytes=rs-512-len(capsule),uncompressed_helper_archive_bytes=len(capsule),
 manifest_records=0,context_block_rules=9,elfs=elfs,legacy_daemon_byte_identical=True,helper_byte_reproduced=True,physical_validation=False)
assert result['reservation_headroom']>0
(R/'evidence/independent-container.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
