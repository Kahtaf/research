"""One offline candidate package; exact baseline, helper, DT and installer pins."""
from pathlib import Path
import ast,difflib,gzip,hashlib,json,shutil,stat,struct,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[1];B=R.parent/'2026-11-08-asus-sparse-watchdog-observation'
def boundary(event,args):
 if event=='open':
  p=str(args[0]);assert not any(x in p for x in ['/private/','/device-backup/','root_shell_wifi.py','mtk-su-mirror-b','/dev/']),p
 if event.startswith(('subprocess.','socket.')) or event in ['os.system','os.posix_spawn']:raise RuntimeError(event)
sys.addaudithook(boundary);sys.path.insert(0,str(R/'source'));import bootformat as b,fdt
rec=lambda d:dict(bytes=len(d),sha256=b.sha(d))
def block(s,name):
 n=next(n for n in ast.parse(s).body if getattr(n,'name',None)==name)
 return ''.join(s.splitlines(True)[n.lineno-1:n.end_lineno])
def diff(a,z):
 assert len(a)==len(z);return [j for j,(x,y) in enumerate(zip(a,z)) if x!=y]
with (R/'evidence/package-attempt.json').open('x') as f:json.dump(dict(one_candidate=True,no_device_or_private_inputs=True),f)
old=(B/'artifacts/candidate.img').read_bytes();current='86213b3aabb8a003ff19157ba5b1dbb29377e0cb14cd70f896fdeccbb944792b'
assert b.sha(old)=='e38c3753630b30bd3ca4d4d67ae49be130621ce7b2bf2d1774b9d78b6711b253' and b.sha(old+bytes(b.PARTITION_SIZE-len(old)))==current
header,kernel,oldram,tail=b.parse_image(old);assert not tail and b.sha(oldram)=='df6406bd884126190ce05c26f097f9d84a36c64e332286fa5aee6225670857d3'
_,runtime=b.ungzip(kernel[512:]);fh,nodes,tokens=fdt.parse(runtime);ch=nodes['/chosen']
compiled=(R/'artifacts/Image.gz-dtb').read_bytes();raw,dt=b.ungzip(compiled);stream=compiled[:-len(dt)]
config=(R/'artifacts/resolved.config').read_bytes();assert config==(B/'artifacts/resolved.config').read_bytes() and b.sha(config)=='708a88175ea777c09410000dfe5cf562ccbf764955eb9deaadda7326d0a966e1'
_,basedt=b.ungzip((B/'artifacts/Image.gz-dtb').read_bytes());assert dt==basedt
_,cn,_=fdt.parse(dt);assert {p:v for p,v in cn.items() if p!='/chosen'}=={p:v for p,v in nodes.items() if p!='/chosen'}
args=b'bootopt=64S3,32N2,64N2 build_version=3 console=null nr_cpus=1 printk.devkmsg=on nohlt'
assert ch['bootargs'].rstrip(b'\0')==header[64:576].rstrip(b'\0')==args and len(args)<92
assert ch['linux,initrd-start']==bytes.fromhex('44000000') and ch['linux,initrd-end']==bytes.fromhex('4403e9d8')
cp,extra=b.ungzip(oldram[512:]);assert not extra;entries=b.parse_cpio(cp)
assert b.sha(entries['init'][3])=='1c9b6f23ed080be753b27ea49158564010a60cf2747e5964f07a2705e3745d1b'
init=(R/'artifacts/init').read_bytes();src=(R/'source/init.c').read_bytes();elf=b.elf_static(init)
receipt=json.loads((R/'evidence/compiler-receipt.json').read_text());assert receipt['source_sha256']==b.sha(src) and receipt['binary_sha256']==b.sha(init)
i=json.loads((R/'evidence/identity.json').read_text());assert i['helper_uuid'].encode() in src and i['helper_uuid'].encode() in init and i['mode'].encode() in raw and ('ASUS49-ENTRY run='+i['kernel_uuid']).encode() in raw
entries['init']=(*entries['init'][:3],init);payload=(R/'artifacts/initramfs.cpio.gz').read_bytes()
actual_cpio,trailing=b.ungzip(payload);assert not trailing and actual_cpio==b.make_cpio(entries) and len(payload)==receipt['payload_bytes']
newend=0x44000000+len(payload);assert newend<=0x4403f007,'STOP: never widen entry guard'
ram=b.wrap(oldram,payload);newdt=bytearray(runtime);pos=fh[2];changed=0
for token,node,name,value,encoded in tokens:
 if (token,node,name)==(3,'/chosen','linux,initrd-end'):
  assert len(value)==4;newdt[pos+12:pos+16]=newend.to_bytes(4,'big');changed+=1
 pos+=len(encoded)
assert changed==1;newdt=bytes(newdt)
nh,nn,nt=fdt.parse(newdt);expected={p:dict(v) for p,v in nodes.items()};expected['/chosen']['linux,initrd-end']=newend.to_bytes(4,'big')
assert nh==fh and nn==expected and newdt[40:fh[2]]==runtime[40:fh[2]]
# Exact token equality except the actual end cell; reservation and hardware bytes unchanged.
for a,z in zip(tokens,nt):
 if a!=z:assert a[:3]==z[:3]==(3,'/chosen','linux,initrd-end') and a[4][:12]==z[4][:12] and a[4][16:]==z[4][16:]
newkernel=b.wrap(kernel,stream+newdt);image=b.make_image(header,newkernel,ram);full=image+bytes(b.PARTITION_SIZE-len(image))
ah,ak,ar,at=b.parse_image(image);rr,rd=b.ungzip(ak[512:]);assert not at and rr==raw and rd==newdt and ar==ram
assert ak[512:-len(rd)]==stream and b.parse_cpio(b.ungzip(ar[512:])[0])==entries
assert newkernel[:4]==kernel[:4] and newkernel[8:512]==kernel[8:512]
assert ram[:4]==oldram[:4] and ram[8:512]==oldram[8:512]
assert set(diff(header,ah))<=set(range(8,12))|set(range(16,20))|set(range(576,608))
assert raw[56:60]==b'ARM\x64';text_offset,image_size=struct.unpack_from('<QQ',raw,8)
ks,ka,rs,ra,ss,sa,ta,page=struct.unpack_from('<8I',ah,8)
assert ka==0x40080000 and ra==0x44000000 and text_offset==0x80000 and page==2048 and ss==0 and image_size>=len(raw)
kend=ka+image_size;assert kend<=ra and kend<=0x44400000 and newend<=0x4403f007<0x44400000
for n,d in [('candidate.img',image),('candidate.p10.raw',full),('runtime.dtb',newdt),('ramdisk.wrapped',ram)]:(R/'artifacts'/n).write_bytes(d)
prior=(B/'source/install.py').read_text();s=prior
pre=next(l for l in s.splitlines() if l.startswith('INSTALL_PREIMAGES='));assert current not in pre
changes={"IMAGE_SHA='e38c3753630b30bd3ca4d4d67ae49be130621ce7b2bf2d1774b9d78b6711b253'":f"IMAGE_SHA='{b.sha(image)}'",f"FULL_SHA='{current}'":f"FULL_SHA='{b.sha(full)}'",'len(image)==7989248':f'len(image)=={len(image)}',"profile='exact-sparse-watchdog-e0b1a1ba-r1'":f"profile='exact-pid1-fifo-{i['kernel_uuid'][:8]}-r1'",pre:pre[:-1]+f",'{current}')"}
for a,z in changes.items():assert s.count(a)==1;s=s.replace(a,z)
restored=s
for a,z in reversed(list(changes.items())):assert restored.count(z)==1;restored=restored.replace(z,a)
assert restored==prior
for n in ['execute','Transport','Guard']:assert block(prior,n)==block(s,n)
(R/'source/install.py').write_text(s);(R/'source/install.diff').write_text(''.join(difflib.unified_diff(prior.splitlines(True),s.splitlines(True),fromfile='baseline/install.py',tofile='fifo/install.py')))
helpers={}
for n in ['bootformat.py','fdt.py','adb','legacy_adb.py']:
 d=(R/'source'/n).read_bytes();assert d==(B/'source'/n).read_bytes();helpers[n]=dict(**rec(d),mode=oct(stat.S_IMODE((R/'source'/n).stat().st_mode)))
assert helpers['adb']['mode']=='0o755'
result=dict(status='ONE_FIFO_DIAGNOSTIC_CANDIDATE_NO_PHYSICAL_TRIAL',kernel_uuid=i['kernel_uuid'],helper_uuid=i['helper_uuid'],candidate=rec(image),full_p10=rec(full),base_full_p10=current,current_pin_supplied_not_freshly_observed=True,config=rec(config),compiled_Image_gz_dtb=rec(compiled),raw_Image=rec(raw),compiled_DTB=rec(dt),prior_runtime_DTB=rec(runtime),runtime_DTB=rec(newdt),init=rec(init),init_source=rec(src),elf=elf,ramdisk=rec(ram),compressed_initramfs=rec(payload),initrd=dict(start=hex(ra),end=hex(newend),payload_bytes=len(payload),wrapper_bytes=512,unchanged_entry_guard_end='0x4403f007',remaining_guard_bytes=0x4403f007-newend),bootargs=args.decode(),layout=dict(Image_image_size=image_size,loaded_Image_end=hex(kend),ramdisk_offset=page+b.align(len(newkernel)),no_overlap=True,android_header_changed_offsets=diff(header,ah),kernel_wrapper_changed_offsets=diff(kernel[:512],newkernel[:512]),ramdisk_wrapper_changed_offsets=diff(oldram[:512],ram[:512])),preservation=dict(config_byte_identical=True,compiled_DT_byte_identical=True,only_runtime_DT_change='chosen/linux,initrd-end actual gzip length',hardware_DT_reservations_tokens_and_short_bootargs_unchanged=True,execute_Transport_Guard_byte_identical=True,adapters=helpers),installer=dict(**rec(s.encode()),changes=['image/full pins','actual image size','profile','append supplied physical-current full p10']),limits=['One helper compile and one incremental kernel build; no physical observation','No bounded walltime; direct clock syscall may stall','RT scheduling changes work ordering and may delay normal-priority protection work; no root-cause inference','Missing records remain unknown publication; restoration and observed policy required','No storage-under-RT/fullOS or automatic next experiment'])
(R/'evidence/packaging-receipt.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ['status','candidate','full_p10','initrd']},indent=2))
