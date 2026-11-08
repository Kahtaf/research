"""One genuine rebuilt kernel package; preserve the entire current ramdisk and DT."""
from pathlib import Path
import ast,difflib,json,shutil,stat,struct,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[1];W=R.parent;B=W/'2026-11-07-asus-linux49-work-dispatch-capture'
def boundary(event,args):
 if event=='open':
  p=str(args[0]);assert not any(x in p for x in ['/private/','/device-backup/','root_shell_wifi.py','mtk-su-mirror-b','/dev/']),p
 if event.startswith(('subprocess.','socket.')) or event in ['os.system','os.posix_spawn']:raise RuntimeError(event)
sys.addaudithook(boundary)
for n in ['bootformat.py','fdt.py','adb','legacy_adb.py']:shutil.copy2(B/'source'/n,R/'source'/n)
sys.path.insert(0,str(R/'source'))
import bootformat as b,fdt
rec=lambda d:dict(bytes=len(d),sha256=b.sha(d))
def diff(a,z):
 assert len(a)==len(z);return [i for i,(x,y) in enumerate(zip(a,z)) if x!=y]
def block(s,name):
 n=next(n for n in ast.parse(s).body if getattr(n,'name',None)==name)
 return ''.join(s.splitlines(True)[n.lineno-1:n.end_lineno])
with (R/'evidence/package-attempt.json').open('x') as out:json.dump(dict(one_genuine_candidate=True,private=False,device=False),out)
old=(B/'artifacts/candidate.img').read_bytes();assert b.sha(old)=='404ec624191bb44a8cf126195addcb18e6835dd1431e025db461a1accca1286f'
current='7418c5d3a43c0b458311d880ec87f0d6b781794998d688153f31c3383f7c3752'
assert b.sha(old+bytes(b.PARTITION_SIZE-len(old)))==current
h,k,ram,tail=b.parse_image(old);assert not tail
oldraw,runtime=b.ungzip(k[512:]);assert b.sha(oldraw)=='68224b50ad7c9a87641c4762a292447954d32f68a8c970fa739f897c663e9a2b'
baseblob=(B/'artifacts/Image.gz-dtb').read_bytes();baseraw,basedt0=b.ungzip(baseblob);assert baseraw==oldraw;assert k[512:-len(runtime)]==baseblob[:-len(basedt0)]
compiled=(R/'artifacts/Image.gz-dtb').read_bytes();config=(R/'artifacts/resolved.config').read_bytes()
assert b.sha(config)=='708a88175ea777c09410000dfe5cf562ccbf764955eb9deaadda7326d0a966e1'
raw,dt=b.ungzip(compiled);stream=compiled[:-len(dt)]
basecompiled=(B/'artifacts/Image.gz-dtb').read_bytes();assert b.sha(basecompiled)=='2d64022664c5ff61296446a41a55186f24247fe9287f03a0ca398a6c26e2e3ab'
_,basedt=b.ungzip(basecompiled);assert dt==basedt
fh,nodes,tokens=fdt.parse(runtime);_,cn,_=fdt.parse(dt)
assert {p:v for p,v in cn.items() if p!='/chosen'}=={p:v for p,v in nodes.items() if p!='/chosen'}
ch=nodes['/chosen'];args=b'bootopt=64S3,32N2,64N2 build_version=3 console=null nr_cpus=1 printk.devkmsg=on nohlt'
assert ch['bootargs'].rstrip(b'\0')==h[64:576].rstrip(b'\0')==args and len(args)<92
assert ch['linux,initrd-start']==bytes.fromhex('44000000') and ch['linux,initrd-end']==bytes.fromhex('4403e9d8')
assert len(ram)-512==256472 and 0x44000000+len(ram)-512==0x4403e9d8<0x4403f007
assert b.sha(ram)=='df6406bd884126190ce05c26f097f9d84a36c64e332286fa5aee6225670857d3'
cp,extra=b.ungzip(ram[512:]);assert not extra;entries=b.parse_cpio(cp);init=entries['init'][3]
assert b.sha(init)=='1c9b6f23ed080be753b27ea49158564010a60cf2747e5964f07a2705e3745d1b' and b'f0c3c82c-d639-4d8a-90f2-155fd4224ceb' in init
identity=json.loads((R/'evidence/identity.json').read_text());linked=json.loads((R/'evidence/linked-capture.json').read_text())
assert identity==linked['entry_identity'] and identity['tag'].encode() in raw
newk=b.wrap(k,stream+runtime);image=b.make_image(h,newk,ram);full=image+bytes(b.PARTITION_SIZE-len(image))
ah,ak,ar,at=b.parse_image(image);rr,rd=b.ungzip(ak[512:]);assert not at and rr==raw and rd==runtime and ar==ram
assert ak[512:-len(rd)]==stream
assert newk[:4]==k[:4] and newk[8:512]==k[8:512]
assert set(diff(h,ah))<=set(range(8,12))|set(range(576,608))
# Linux ARM64 image_size includes BSS. Apply existing load/reservation contract
# to the actual rebuilt Image and the unchanged LK header/wrapper geometry.
assert raw[56:60]==b'ARM\x64';text_offset,image_size=struct.unpack_from('<QQ',raw,8)
ks,ka,rs,ra,ss,sa,ta,page=struct.unpack_from('<8I',ah,8)
assert ka==0x40080000 and ra==0x44000000 and text_offset==0x80000 and page==2048 and ss==0
assert image_size==linked['Image']['image_size'] and image_size>=len(raw)
kend=ka+image_size
assert kend<=ra and kend<=0x44400000 and kend<0xbd600000
regions=[('loaded Image including BSS',ka,kend),('initrd payload',ra,ra+len(ram)-512),('retained console',0x44400000,0x44480000)]
for i,(n,a,z) in enumerate(regions):
 for m,aa,zz in regions[i+1:]:assert not (a<zz and aa<z),(n,m)
layout=dict(android_header_u32_fields=list(struct.unpack_from('<10I',ah,8)),kernel_offset=page,kernel_bytes=len(newk),ramdisk_offset=page+b.align(len(newk)),ramdisk_bytes=len(ram),ramdisk_payload_bytes=len(ram)-512,raw_Image_bytes=len(raw),Image_text_offset=hex(text_offset),Image_image_size=image_size,loaded_Image_start=hex(ka),loaded_Image_end=hex(kend),android_tags_address=hex(ta),boot_id=ah[576:608].hex(),LK_contract='512-byte MTK wrappers retained; LK strips ramdisk wrapper; unchanged chosen initrd bounds describe compressed payload; actual Image.image_size checked for kernel/initrd/console overlap',no_overlaps=True,runtime_DTB_byte_identical=True,compiled_DTB_byte_identical=True)
for n,d in [('candidate.img',image),('candidate.p10.raw',full),('runtime.dtb',runtime),('ramdisk.wrapped',ram)]:(R/'artifacts'/n).write_bytes(d)
prior=(B/'source/install.py').read_text();s=prior
pre=next(l for l in s.splitlines() if l.startswith('INSTALL_PREIMAGES='));assert current not in pre
profile=next(l for l in s.splitlines() if "profile='" in l)
changes={"IMAGE_SHA='404ec624191bb44a8cf126195addcb18e6835dd1431e025db461a1accca1286f'":f"IMAGE_SHA='{b.sha(image)}'",f"FULL_SHA='{current}'":f"FULL_SHA='{b.sha(full)}'",'len(image)==7981056':f'len(image)=={len(image)}',profile:profile.replace('exact-linux49-work-dispatch-b4702f9a-r1','exact-linux49-power-supply-phase-431dfb9c-r1'),pre:pre[:-1]+f",'{current}')"}
for a,z in changes.items():assert s.count(a)==1;s=s.replace(a,z)
restored=s
for a,z in reversed(list(changes.items())):assert restored.count(z)==1;restored=restored.replace(z,a)
assert restored==prior
for n in ['execute','Transport','Guard']:assert block(prior,n)==block(s,n)
(R/'source/install.py').write_text(s);(R/'source/install.diff').write_text(''.join(difflib.unified_diff(prior.splitlines(True),s.splitlines(True),fromfile='work-dispatch-capture/source/install.py',tofile='power-supply-phase-capture/source/install.py')))
helpers={}
for n in ['bootformat.py','fdt.py','adb','legacy_adb.py']:
 d=(R/'source'/n).read_bytes();assert d==(B/'source'/n).read_bytes();helpers[n]=dict(**rec(d),mode=oct(stat.S_IMODE((R/'source'/n).stat().st_mode)))
assert helpers['adb']['mode']=='0o755'
result=dict(status='ONE_DIAGNOSTIC_POWER_PHASE_CANDIDATE_NO_PHYSICAL_GO',run_uuid=identity['run_uuid'],candidate=rec(image),full_p10=rec(full),base_candidate=rec(old),admitted_current_full_p10=current,current_pin_supplied_not_freshly_observed=True,compiled_Image_gz_dtb=rec(compiled),compressed_Image=rec(stream),raw_Image=rec(raw),config=rec(config),compiled_DTB=rec(dt),runtime_DTB=rec(runtime),ramdisk=rec(ram),init=rec(init),helper_uuid='f0c3c82c-d639-4d8a-90f2-155fd4224ceb',bootargs=args.decode(),initrd=dict(start='0x44000000',end='0x4403e9d8',payload_bytes=256472,wrapper_bytes=512,unchanged_entry_guard_end='0x4403f007'),preservation=dict(config_byte_identical=True,entire_wrapped_ramdisk_byte_identical=True,runtime_DT_byte_identical=True,compiled_DT_byte_identical=True,hardware_reservations_addresses_bounds_and_short_bootargs_unchanged=True,execute_Transport_Guard_byte_identical=True,adapters=helpers),installer=dict(**rec(s.encode()),changes=['actual image hash','full p10 hash','actual image size','profile','append current full p10']),Android_header_changed_offsets=diff(h,ah),kernel_wrapper_changed_offsets=diff(k[:512],newk[:512]),layout=layout,limits=['Source/ELF/host/PLAN checks do not establish physical capture or cause','Capture overhead can perturb timing; entry without exit is a captured boundary only','Dropped/torn/early-unavailable capture is UNKNOWN','No device/private payload or raw target log access'])
(R/'evidence/packaging-receipt.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ['status','run_uuid','candidate','full_p10','raw_Image','compiled_Image_gz_dtb']},indent=2))
