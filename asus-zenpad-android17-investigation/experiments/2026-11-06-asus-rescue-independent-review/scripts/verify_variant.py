"""Independent bounded image parser and context delta audit; never opens OS/data payloads."""
import collections,gzip,hashlib,importlib.util,json,struct
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R.parent/'2026-11-06-asus-android17-target-rescue';F=R.parent/'2026-11-06-asus-rescue-block-context-fix'
sha=lambda b:hashlib.sha256(b).hexdigest()
def aligned(n,p=2048):return (n+p-1)//p*p
def unpack(path):
 b=path.read_bytes();assert b[:8]==b'ANDROID!'
 ks,ka,rs,ra,ss,sa,tags,page=struct.unpack_from('<8I',b,8);assert page==2048 and ss==0
 ko=page;ro=ko+aligned(ks);assert len(b)==ro+aligned(rs)
 k=b[ko:ko+ks];r=b[ro:ro+rs]
 for x in [k,r]:assert x[:4]==bytes.fromhex('88168858') and struct.unpack_from('<I',x,4)[0]==len(x)-512
 assert not any(b[ko+ks:ro]) and not any(b[ro+rs:])
 s=hashlib.sha1();s.update(k);s.update(struct.pack('<I',ks));s.update(r);s.update(struct.pack('<I',rs));s.update(struct.pack('<I',0));assert b[576:596]==s.digest()
 raw=gzip.decompress(r[512:]);entries={};p=0
 while True:
  assert raw[p:p+6]==b'070701';fields=[int(raw[p+6+i*8:p+14+i*8],16) for i in range(13)]
  mode,uid,gid,size,namesize=fields[1],fields[2],fields[3],fields[6],fields[11]
  name=raw[p+110:p+110+namesize];assert name[-1:]==b'\0';name=name[:-1].decode();p=aligned(p+110+namesize,4)
  data=raw[p:p+size];assert len(data)==size;p=aligned(p+size,4)
  if name=='TRAILER!!!':break
  assert name not in entries;entries[name]=(mode,uid,gid,data)
 assert not any(raw[p:])
 return b,k,r,entries,dict(kernel_address=hex(ka),ramdisk_address=hex(ra),tags_address=hex(tags),ramdisk_payload_bytes=len(r)-512)
old,ok,orr,oe,om=unpack(D/'artifacts/candidate-delivery/UNTESTED-target-rescue.img')
new,nk,nr,ne,nm=unpack(F/'artifacts/candidate-kind-fix/UNTESTED-target-rescue-block-kinds.img')
assert sha(old)=='93d647ea58784aefe4104cb0cbddbac04fe6169b30923ad63c5684e0dc920419'
assert sha(new)=='299e65cbc1b5290b1e9ef89e0495ca5b8eac63d0d6e486d15611624ba63d35ea'
assert nk==ok and new[64:576]==old[64:576] and set(oe)==set(ne)
changed=[n for n in oe if oe[n]!=ne[n]];assert changed==['file_contexts.bin']
assert oe['file_contexts.bin'][:3]==ne['file_contexts.bin'][:3]
assert sha(ne['file_contexts.bin'][3])=='7723428608524a84b06144e4d48836c65219fe48503f230070567063b50b3f89'
assert sha(ne['sepolicy'][3])=='189c477ac73ecb161a6527f7f98a6fec76a913b0d5cf8d11591d440dc79af842'
assert ne['rescue.manifest'][3][:16]==b'ASUSR002\x02\0\0\0\0\0\0\0' and len(ne['rescue.manifest'][3])==112
assert len(new)<16740352 and len(nr)-512<0x400000
padded=hashlib.sha256();padded.update(new);padded.update(bytes(16740352-len(new)))
assert padded.hexdigest()=='225151bafbb86d0b72abd72299888524b13cb8b651bec7d7b617dc0cbc913f6b'
# Use original decoder for the compiled regex table only; all container parsing above is independent.
p=D/'source/file_contexts.py';spec=importlib.util.spec_from_file_location('decoder',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
a,b=m.extract(oe['file_contexts.bin'][3]),m.extract(ne['file_contexts.bin'][3]);delta=collections.Counter(a);rows=[]
for row in a:
 if row[2].split(':')[2].startswith('rescue_') and row[2].split(':')[2].endswith('_device'):
  assert row[1]=='';delta[row]-=1;delta[(row[0],'-b',row[2])]+=1;rows.append(row[0])
assert len(rows)==9 and +delta==collections.Counter(b)
# Preserve only bounded metadata, no executable/ramdisk duplicate.
report={'passed':True,'image_sha256':sha(new),'image_bytes':len(new),'padded_p10_sha256':padded.hexdigest(),'changed_cpio_entries':changed,'changed_context_rows':rows,'context_rows':len(b),'contexts_sha256':sha(ne['file_contexts.bin'][3]),'policy_sha256':sha(ne['sepolicy'][3]),'kernel_sha256':sha(nk),'manifest_records':0,'manifest_bytes':112,'all_other_cpio_metadata_and_bytes_identical':True,'header_cmdline':new[64:576].split(b'\0')[0].decode(),'ueventd_entry':{'mode':oct(ne['sbin/ueventd'][0]),'symlink_target':ne['sbin/ueventd'][3].decode()},'init_sha256':sha(ne['init'][3]),'component_geometry':nm,'reservation_headroom_bytes':0x400000-(len(nr)-512),'p10_headroom_bytes':16740352-len(new),'context_decoder_sha256':sha(p.read_bytes()),'physical_validation':False,'large_payloads_read':False}
(R/'evidence/variant-independent.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
