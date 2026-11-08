"""Independent fixed-candidate parser. Never imports implementation or accesses devices."""
from pathlib import Path
import struct as S,zlib,hashlib as H,json,posixpath
R=Path(__file__).resolve().parents[1];W=R.parent;B=W/'2026-11-06-asus-android17-build-continuation';O=R/'evidence';X=R/'source/ramdisk';X.mkdir(exist_ok=True)
sha=lambda b:H.sha256(b).hexdigest()
align=lambda n,a:(n+a-1)//a*a
pins={}
def read(p):
 b=p.read_bytes();pins[str(p.relative_to(W))]={'bytes':len(b),'sha256':sha(b)};return b

def boot(b,full=False):
 assert b[:8]==b'ANDROID!' and len(b)<=16740352
 ks,ka,rs,ra,ss,sa,ta,ps,ver,osv=S.unpack_from('<10I',b,8)
 assert (ka,ra,ss,sa,ta,ps,ver,osv)==(0x40080000,0x44000000,0,0x40f00000,0x4e000000,2048,0,0x0e000126)
 ko=ps;ro=ko+align(ks,ps);end=ro+align(rs,ps);assert end<=len(b)
 assert not any(b[ko+ks:ro]) and not any(b[ro+rs:end])
 if not full:assert not any(b[end:])
 if not full:assert end==len(b)
 k=b[ko:ko+ks];r=b[ro:ro+rs]
 assert b[576:608]==H.sha1(k+S.pack('<I',ks)+r+S.pack('<II',rs,0)).digest()+bytes(12)
 for c,label in [(k,b'KERNEL'),(r,b'RECOVERY')]:
  assert S.unpack_from('<II',c)==(0x58881688,len(c)-512)
  assert c[8:40].split(b'\0')[0]==label
 return b[:ps],k,r,{'kernel_size_including_wrapper':ks,'ramdisk_size_including_wrapper':rs,'ramdisk_file_offset':ro,'unpadded_bytes':end}

def gz(b,cap):
 d=zlib.decompressobj(31);r=d.decompress(b,cap+1)
 assert len(r)<=cap and d.eof and not d.unconsumed_tail
 consumed=len(b)-len(d.unused_data);crc,n=S.unpack_from('<II',b,consumed-8)
 assert crc==zlib.crc32(r) and n==len(r)%(2**32)
 return r,b[consumed:],b[:consumed],{'compressed_bytes':consumed,'raw_bytes':len(r),'crc32':hex(crc)}

def cpio(b,strict=True):
 pos=0;entries={};inos=set()
 while True:
  assert pos+110<=len(b) and b[pos:pos+6]==b'070701'
  f=[int(b[pos+6+i*8:pos+14+i*8],16) for i in range(13)]
  ino,mode,uid,gid,nlink,mtime,size,devmaj,devmin,rmaj,rmin,ns,check=f
  assert 0<ns<=4096 and size<=16*1024**2 and not check
  nb=b[pos+110:pos+110+ns];assert nb[-1:]==b'\0' and b'\0' not in nb[:-1]
  name=nb[:-1].decode();start=align(pos+110+ns,4);stop=start+size;assert stop<=len(b)
  assert not any(b[pos+110+ns:start]) and not any(b[stop:align(stop,4)])
  value=b[start:stop];pos=align(stop,4)
  if name=='TRAILER!!!':assert size==0 and not any(b[pos:]);break
  assert name and not name.startswith('/') and name==posixpath.normpath(name) and '..' not in name.split('/') and name not in entries
  assert ino not in inos;inos.add(ino)
  kind=mode&0o170000;assert kind in (0o040000,0o100000,0o120000) and not(mode&0o6000)
  assert uid==gid==0 and rmaj==rmin==0
  assert not strict or nlink==(2 if kind==0o040000 else 1)
  if kind==0o040000:assert not value
  if strict and kind==0o120000:
   target=value.decode();resolved=posixpath.normpath(posixpath.join(posixpath.dirname(name),target))
   assert not target.startswith('/') and not resolved.startswith('../')
  entries[name]={'mode':oct(mode),'uid':uid,'gid':gid,'bytes':size,'sha256':sha(value),'data':value}
 for n,v in entries.items():
  parent=posixpath.dirname(n)
  if parent:assert parent in entries and int(entries[parent]['mode'],8)&0o170000==0o040000
  if strict and int(v['mode'],8)&0o170000==0o120000:assert posixpath.normpath(posixpath.join(posixpath.dirname(n),v['data'].decode())) in entries
 return entries

def fdt(b):
 h=S.unpack_from('>10I',b);magic,total,so,stro,mo,version,last,cpuid,strsz,ssz=h
 assert magic==0xd00dfeed and total==len(b) and version==17 and last<=17
 assert 40<=mo<so and so+ssz<=len(b) and stro+strsz<=len(b)
 mem=[];p=mo
 while True:
  a,n=S.unpack_from('>QQ',b,p);p+=16
  if a==n==0:break
  mem.append([a,n])
 assert p<=so
 strings=b[stro:stro+strsz];props={};stack=[];p=so
 while p<so+ssz:
  token=S.unpack_from('>I',b,p)[0];p+=4
  if token==1:
   end=b.index(b'\0',p,so+ssz);name=b[p:end].decode();p=align(end+1,4);stack.append(name);node='/'.join(stack) or '/';assert node not in props;props[node]={}
  elif token==2:assert stack;stack.pop()
  elif token==3:
   n,off=S.unpack_from('>II',b,p);p+=8;assert off<len(strings) and p+n<=so+ssz
   key=strings[off:strings.index(b'\0',off)].decode();node='/'.join(stack) or '/';assert key not in props[node];props[node][key]=b[p:p+n];p=align(p+n,4)
  elif token==4:pass
  elif token==9:assert not stack and p==so+ssz;break
  else:raise AssertionError(token)
 return props,mem,h

candidate=read(B/'artifacts/probe-r2/UNTESTED-combined-linux49-ram-probe.img');assert sha(candidate)=='48bb6efa1620cb380037e53b53cfa560e38cd23b95211c8634616ce94fd6ce48'
compiled=read(B/'artifacts/Image.gz-dtb-combined-r1');assert sha(compiled)=='d4094bcff6c763af7f1c01ccd3d612a988f96de13f78b492b808cc76c0ac929f'
stock=read(W/'2026-11-05-asus-boot-access-audit/artifacts/device-backup/initial/recovery.bin');assert sha(stock)=='902b2f06a01cca574b4aa374e67c4e7f8f0ed53f6e6a55017b6d96351f0f1f20'
stock2=read(W/'2026-11-05-asus-boot-access-audit/artifacts/device-backup/verify/recovery.bin');assert stock==stock2
control=read(W/'2026-11-06-asus-android17-os-rescue/artifacts/candidate-final/UNTESTED-stock-control.img');assert sha(control)=='7d74dfcaf4b2793453906799d721bfd95a401c564f6698b1c646e18bee918ea5'
h,k,r,geometry=boot(candidate);sh,sk,sr,_=boot(stock,True);ch,ck,cr,_=boot(control)
assert h[:8]==sh[:8] and h[12:16]==sh[12:16] and h[20:64]==sh[20:64] and h[608:]==sh[608:]
raw,dt,kstream,kinfo=gz(k[512:],64*1024**2);oldraw,olddt,oldstream,_=gz(compiled,64*1024**2)
assert raw==oldraw and kstream==oldstream
ram,tail,rstream,rinfo=gz(r[512:],16*1024**2);assert not tail
assert rstream==(B/'artifacts/probe-r2/diagnostic.cpio.gz').read_bytes()
assert dt==(B/'artifacts/probe-r2/packaged.dtb').read_bytes()
entries=cpio(ram);original=cpio(gz(sr[512:],16*1024**2)[0],False);repaired=cpio(gz(cr[512:],16*1024**2)[0])
assert original['sepolicy']['data']==(W/'2026-11-06-asus-android17-os-rescue/artifacts/candidate-final/stock-sepolicy').read_bytes()
for n in ['init','sbin/adbd','file_contexts.bin','property_contexts','seapp_contexts','service_contexts']:
 assert entries[n]==original[n],n
assert entries['adb_keys']==repaired['adb_keys']
assert entries['sbin/ueventd']['data']==b'../init';assert entries['system/bin/sh']['data']==entries['sbin/recovery']['data']
for n,v in entries.items():
 if int(v['mode'],8)&0o170000==0o100000:
  p=X/n;p.parent.mkdir(exist_ok=True,parents=True);p.write_bytes(v['data'])
props,mem,fh=fdt(dt);oprops,omem,oh=fdt(olddt);assert mem==omem
assert dt[40:fh[2]]==olddt[40:oh[2]]
delta=[(n,p) for n in props.keys()|oprops.keys() for p in props.get(n,{}).keys()|oprops.get(n,{}).keys() if props.get(n,{}).get(p)!=oprops.get(n,{}).get(p)]
assert set(delta)=={('/chosen','bootargs'),('/chosen','linux,initrd-start'),('/chosen','linux,initrd-end')}
size=len(r)-512;start=0x44000200;end=start+size;token=f'initrd=0x{start:x},0x{size:x}'.encode()
for cmd in [h[64:576].split(b'\0')[0],props['/chosen']['bootargs'].rstrip(b'\0')]:assert [t for t in cmd.split() if t.startswith(b'initrd=')]==[token]
assert not any(h[608:1632]);assert int.from_bytes(props['/chosen']['linux,initrd-start'],'big')==start and int.from_bytes(props['/chosen']['linux,initrd-end'],'big')==end
assert all('asus,allow-battery-charging' not in p for p in props.values())
for name,expected in {'rbat_pull_up_r':16900,'rbat_pull_down_r':30000,'rbat_pull_up_volt':1800,'vbat_channel_number':6,'isense_channel_number':7,'vcharger_channel_number':4,'vbattemp_channel_number':5,'swchr_power_path':1}.items():assert int.from_bytes(props['/soc/bat_meter'][name],'big')==expected
assert raw[56:60]==b'ARM\x64';offset,image_size,flags=S.unpack_from('<QQQ',raw,8)
assert offset==0x80000 and image_size>=len(raw) and 0x40080000+image_size<0x44000000 and end<0x4e000000
assert k[:4]+k[8:512]==sk[:4]+sk[8:512] and r[:4]+r[8:512]==sr[:4]+sr[8:512]
elf={}
for n in ['init','sbin/adbd','sbin/recovery','system/bin/sh']:
 b=entries[n]['data'];assert b[:6]==b'\x7fELF\x02\x01' and S.unpack_from('<H',b,18)[0]==183
 off=S.unpack_from('<Q',b,32)[0];ents,count=S.unpack_from('<HH',b,54);assert ents==56
 seg=[S.unpack_from('<IIQQQQQQ',b,off+i*ents) for i in range(count)];assert all(s[0] not in (2,3) for s in seg)
 assert all(s[2]+s[5]<=len(b) and s[5]<=s[6] for s in seg if s[0]==1)
 elf[n]={'sha256':sha(b),'aarch64_static':True,'entry':hex(S.unpack_from('<Q',b,24)[0])}
full=candidate+bytes(16740352-len(candidate));assert sha(full)=='25812e7dde39ec37e3f4c9438341cc29f2b2e7dce61e4b88d0886cd9dd075b16'
manifest=json.loads((B/'artifacts/probe-r2/manifest.json').read_text())
assert manifest['image_sha256']==sha(candidate) and manifest['input_kernel_sha256']==sha(compiled)
assert manifest['entries']=={n:{k:v for k,v in e.items() if k!='data'} for n,e in entries.items()}
summary={'status':'STATIC_PACKAGING_PASS_ONLY','candidate_sha256':sha(candidate),'candidate_bytes':len(candidate),'padded_sha256':sha(full),'compiled_sha256':sha(compiled),'geometry':geometry,'kernel_stream':kinfo,'ramdisk_stream':rinfo,'initrd_range':[hex(start),hex(end)],'image_header':{'text_offset':hex(offset),'image_size':image_size,'flags':hex(flags),'kernel_memory_end':hex(0x40080000+image_size)},'dt_changed_properties':sorted(delta),'dt_reservations':mem,'cmdline':h[64:576].split(b'\0')[0].decode(),'chosen_bootargs':props['/chosen']['bootargs'].rstrip(b'\0').decode(),'elf':elf,'stock_preserved':['init','sbin/adbd','file_contexts.bin','property_contexts','seapp_contexts','service_contexts'],'changes_vs_repaired_control':sorted(n for n in entries.keys()|repaired.keys() if entries.get(n)!=repaired.get(n)),'entries':{n:{k:v for k,v in e.items() if k!='data'} for n,e in entries.items()},'physical_boot_proven':False}
(O/'artifact-inspection.json').write_text(json.dumps(summary,indent=2)+'\n');(O/'artifact-input-pins.json').write_text(json.dumps(pins,indent=2)+'\n');(O/'packaged-dt-properties.json').write_text(json.dumps({n:{k:v.hex() for k,v in p.items()} for n,p in props.items()},indent=2)+'\n');print(json.dumps({k:v for k,v in summary.items() if k not in ('entries','elf')},indent=2))
