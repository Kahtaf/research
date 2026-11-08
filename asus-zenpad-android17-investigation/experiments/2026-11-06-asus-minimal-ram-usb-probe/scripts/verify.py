"""Independent byte readers: validate the emitted boot container and FAT fixture."""
from pathlib import Path
import struct,json,zlib,hashlib
R=Path(__file__).resolve().parents[1];A=R/'artifacts';H=lambda b:hashlib.sha256(b).hexdigest()
def fat_check(b):
 assert len(b)==65536 and b[510:512]==b'\x55\xaa'
 sec=struct.unpack_from('<H',b,11)[0];spc=b[13];reserved=struct.unpack_from('<H',b,14)[0];nf=b[16];roots=struct.unpack_from('<H',b,17)[0];total=struct.unpack_from('<H',b,19)[0];spf=struct.unpack_from('<H',b,22)[0]
 assert (sec,spc,reserved,nf,roots,total,spf)==(512,1,1,2,32,128,1)
 f1=b[reserved*sec:(reserved+spf)*sec];assert f1==b[(reserved+spf)*sec:(reserved+2*spf)*sec] and f1[:3]==b'\xf8\xff\xff'
 ro=(reserved+nf*spf)*sec;data=ro+roots*32;root=b[ro:data];entries=[]
 for i in range(0,len(root),32):
  e=root[i:i+32]
  if not e[0]:break
  entries.append(e)
 assert len(entries)==2 and entries[0][:11]==b'RAMPROBE   ' and entries[0][11]==8
 e=entries[1];assert e[:11]==b'REPORT  TXT' and e[11]==1
 n=struct.unpack_from('<I',e,28)[0];c=struct.unpack_from('<H',e,26)[0];seen=set();payload=b''
 while c<0xff8:
  assert 2<=c<125 and c not in seen;seen.add(c);payload+=b[data+(c-2)*sec:data+(c-1)*sec]
  v=struct.unpack_from('<H',f1,c+c//2)[0];c=(v>>4 if c&1 else v&0xfff)
 assert c==0xfff and n<=len(payload) and not any(payload[n:]);report=payload[:n].decode('ascii')
 pairs=dict(line.split('=',1) for line in report.splitlines())
 assert set(pairs)=={'run_id','pid1','sysname','release','version','machine','status'}
 assert pairs['run_id']=='b8bfa53e-4142-4ec8-b603-8f25cb617e2e' and pairs['pid1']=='1' and pairs['status']=='pid1_ram_report_ready'
 for c in range(2,125):
  if c not in seen:
   v=struct.unpack_from('<H',f1,c+c//2)[0];assert (v>>4 if c&1 else v&0xfff)==0
 return {'bytes':len(b),'sha256':H(b),'report':pairs,'clusters':sorted(seen),'two_fats_identical':True,'readonly_directory_attribute':True}
b=(A/'candidate.img').read_bytes();h=(R/'inputs/original-header').read_bytes();w=(R/'inputs/original-wrapper').read_bytes()
assert b[:8]==b'ANDROID!' and len(b)<16*1024**2
ks,ka,rs,ra,ss,sa,ta,page,dt,unused=struct.unpack_from('<10I',b,8);assert page==2048 and ss==dt==0
al=lambda n:(n+page-1)//page*page
ro=page+al(ks);end=ro+al(rs);assert len(b)==end
k=b[page:page+ks];ram=b[ro:ro+rs]
assert H(k)=='b0e5d48bf2889b418dda0fc867f70e42e27a0aeb0a0a3d37539d9a7435430880'
for actual,template,allowed in [(b[:page],h,set(range(8,12))|set(range(16,20))|set(range(576,608))),(ram[:512],w,set(range(4,8)))]:
 assert all(i in allowed or x==y for i,(x,y) in enumerate(zip(actual,template)))
assert ram[:4]==bytes.fromhex('88168858') and struct.unpack_from('<I',ram,4)[0]==rs-512
assert b[576:608]==hashlib.sha1(k+struct.pack('<I',ks)+ram+struct.pack('<II',rs,0)).digest()+bytes(12)
assert not any(b[page+ks:ro]) and not any(b[ro+rs:end])
d=zlib.decompressobj(31);cp=d.decompress(ram[512:],2*1024**2);assert d.eof and not d.unused_data and not d.unconsumed_tail
p=0;entries={}
while True:
 assert cp[p:p+6]==b'070701';f=[int(cp[p+6+8*i:p+14+8*i],16) for i in range(13)];ns=f[11];size=f[6];assert 0<ns<100 and size<2*1024**2
 name=cp[p+110:p+110+ns-1].decode();assert cp[p+110+ns-1]==0;p=(p+110+ns+3)//4*4;v=cp[p:p+size];assert len(v)==size;p=(p+size+3)//4*4
 if name=='TRAILER!!!':assert size==0 and not any(cp[p:]);break
 assert name not in entries and f[2]==f[3]==f[5]==0;entries[name]={'mode':f[1],'bytes':size,'sha256':H(v)}
 if name=='init':elf=v
assert set(entries)=={'init','dev','proc','sys'} and entries['init']['mode']==0o100755
assert elf[:6]==b'\x7fELF\x02\x01' and struct.unpack_from('<HH',elf,16)==(2,183)
phoff=struct.unpack_from('<Q',elf,32)[0];phsz,phnum=struct.unpack_from('<HH',elf,54)
types=[struct.unpack_from('<I',elf,phoff+i*phsz)[0] for i in range(phnum)];assert 2 not in types and 3 not in types and 1 in types
entry=struct.unpack_from('<Q',elf,24)[0];assert any(struct.unpack_from('<I',elf,phoff+i*phsz)[0]==1 and struct.unpack_from('<I',elf,phoff+i*phsz+4)[0]&1 and struct.unpack_from('<Q',elf,phoff+i*phsz+16)[0]<=entry<struct.unpack_from('<Q',elf,phoff+i*phsz+16)[0]+struct.unpack_from('<Q',elf,phoff+i*phsz+40)[0] for i in range(phnum))
assert ram[512:514]==b'\x1f\x8b' and len(ram)-512<0x200000
# Static chosen bound, historical DT start, and header load all contain the tiny stream.
assert ra==0x44000000 and ra+rs<0x44200000 and ra+rs<0x44400000
pad=b+bytes(16740352-len(b));assert (A/'candidate.p10.raw').read_bytes()==pad
r={'passed':True,'candidate':{'bytes':len(b),'sha256':H(b)},'p10':{'bytes':len(pad),'sha256':H(pad)},'kernel':{'bytes':len(k),'sha256':H(k)},'ramdisk':{'offset':ro,'wrapped_bytes':rs,'gzip_bytes':rs-512,'expanded_cpio_bytes':len(cp),'single_gzip_member':True,'entries':entries,'load_address':hex(ra),'wrapped_end':hex(ra+rs),'payload_if_wrapper_stripped_start':hex(ra+512),'payload_if_wrapper_stripped_end':hex(ra+rs),'static_2MiB_bound_fit':True,'runtime_initrd_bounds_observed':False},'elf':{'static':True,'machine':'AArch64','entry':hex(entry),'program_header_types':types},'fat':fat_check((A/'report-fixture.fat').read_bytes())}
(R/'evidence/independent-validation.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
