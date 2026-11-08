"""One offline package/preservation unit; no device, private inputs or processes."""
from pathlib import Path
import ast,difflib,gzip,hashlib,json,shutil,stat,struct,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[1];W=R.parent;BASE=W/'2026-11-07-asus-linux49-runnable-timer-format-fix';KBASE=W/'2026-11-07-asus-linux49-ram-primitive-probe'
def boundary(event,args):
 if event=='open':
  p=str(args[0]);assert not any(x in p for x in ['/private/','/device-backup/','root_shell_wifi.py','mtk-su-mirror-b','/dev/']),p
 if event.startswith(('subprocess.','socket.')) or event in ['os.system','os.posix_spawn']:raise RuntimeError(event)
sys.addaudithook(boundary);sys.path.insert(0,str(R/'source'))
import bootformat as b,fdt
rec=lambda d:dict(bytes=len(d),sha256=b.sha(d))
def block(s,name):
 n=next(n for n in ast.parse(s).body if getattr(n,'name',None)==name)
 return ''.join(s.splitlines(True)[n.lineno-1:n.end_lineno])
def diff(a,z):
 assert len(a)==len(z);return [i for i,(x,y) in enumerate(zip(a,z)) if x!=y]
with (R/'evidence/package-attempt.json').open('x') as out:json.dump(dict(one_candidate=True,private=False,device=False),out)
old=(BASE/'artifacts/candidate.img').read_bytes();assert len(old)==7974912;assert b.sha(old)=='13033865fe5c88952efe2d5e429246a76a08689be604fb89a4776afa990c4ab8'
current='88f79cc02d71bfe0708d6be77d66d06d3107befcee3d5d0225ecc8134942f617'
assert b.sha(old+bytes(b.PARTITION_SIZE-len(old)))==current
assert (BASE/'artifacts/candidate.p10.raw').read_bytes()==old+bytes(b.PARTITION_SIZE-len(old))
header,kernel,oldram,tail=b.parse_image(old);assert not tail
compiled=(KBASE/'artifacts/Image.gz-dtb').read_bytes();config=(KBASE/'artifacts/resolved.config').read_bytes()
assert b.sha(compiled)=='97b7e1199d607f852bf52ff7766e8aa079fee92986cd3d473b765a45adbf45fb'
assert b.sha(config)=='708a88175ea777c09410000dfe5cf562ccbf764955eb9deaadda7326d0a966e1'
raw,dt=b.ungzip(kernel[512:]);compiled_raw,compiled_dt=b.ungzip(compiled)
stream=kernel[512:-len(dt)];assert raw==compiled_raw and stream==compiled[:-len(compiled_dt)]
assert b.sha(stream)=='29437894a38cba034db136aa5ea3f1c930edf6ff6abcfc14a4dd652ceeebc491'
assert b.sha(raw)=='60755a9910450cb0303157017ddb4f6ff08874fca32bf70298bb5a91d5450381'
h,nodes,tokens=fdt.parse(dt);ch=nodes['/chosen']
assert ch['linux,initrd-start']==bytes.fromhex('44000000') and ch['linux,initrd-end']==bytes.fromhex('4403e975')
assert ch['bootargs'].rstrip(b'\0')==header[64:576].rstrip(b'\0')
assert not any(x.startswith(b'initrd=') for x in ch['bootargs'].split())
# Explicit source scope was checked before compile; bind exact checked source here.
source=(R/'source/init.c').read_bytes()
scope=json.loads((R/'evidence/source-scope-receipt.json').read_text())
assert scope['source_sha256']==b.sha(source)
assert scope['exact_declared_source_delta'] and scope['all_other_functions_unchanged']
assert scope['no_handler_reboot'] and scope['one_normal_reboot']
assert scope['interrupt_bounds']==dict(bytes=32768,read_calls=8,lines=256,arch_lines=8,cpu_counters=16)
assert scope['loop_bounds']==dict(iterations=2000000,counter_delta_ns=1500000000)
args=ch['bootargs'].rstrip(b'\0');assert len(args)<92
assert args.split().count(b'nohlt')==1 and args.split().count(b'printk.devkmsg=on')==1
init=(R/'artifacts/init').read_bytes();elf=b.elf_static(init);src=(R/'source/init.c').read_bytes()
uuid=json.loads((R/'evidence/identity.json').read_text())['pid1_run_uuid'];assert uuid.encode() in src and uuid.encode() in init
receipt=json.loads((R/'evidence/compiler-receipt.json').read_text());assert receipt['exit']==0 and receipt['source_sha256']==b.sha(src) and receipt['binary_sha256']==b.sha(init)
entries={n:(0o040755,0,0,b'') for n in ['dev','proc','sys']};entries['init']=(0o100755,0,0,init)
cpio=b.make_cpio(entries);payload=gzip.compress(cpio,compresslevel=9,mtime=0)
(R/'evidence/ramdisk-size.json').write_text(json.dumps(dict(compressed_payload_bytes=len(payload),limit=258055,within_limit=len(payload)<=258055),indent=2)+'\n')
assert len(payload)<=258055,'Stop: compressed initramfs exceeds existing assembly guard'
ram=b.wrap(oldram,payload);newend=0x44000000+len(payload)
newdt=bytearray(dt);pos=h[2];changed=0
for t,node,name,value,encoded in tokens:
 if (t,node,name)==(3,'/chosen','linux,initrd-end'):
  assert len(value)==4;newdt[pos+12:pos+16]=newend.to_bytes(4,'big');changed+=1
 pos+=len(encoded)
assert changed==1;newdt=bytes(newdt)
nh,newnodes,newtokens=fdt.parse(newdt);expected={p:dict(v) for p,v in nodes.items()};expected['/chosen']['linux,initrd-end']=newend.to_bytes(4,'big')
assert nh==h and newnodes==expected and newdt[40:h[2]]==dt[40:h[2]]
for a,z in zip(tokens,newtokens):
 if a!=z:assert a[:3]==z[:3]==(3,'/chosen','linux,initrd-end') and a[4][:12]==z[4][:12] and a[4][16:]==z[4][16:]
_,cn,ct=fdt.parse(compiled_dt)
assert {p:v for p,v in cn.items() if p!='/chosen'}=={p:v for p,v in newnodes.items() if p!='/chosen'}
newkernel=b.wrap(kernel,stream+newdt);assert newkernel[:512]==kernel[:512]
image=b.make_image(header,newkernel,ram);full=image+bytes(b.PARTITION_SIZE-len(image));assert len(full)==16740352
ah,ak,ar,at=b.parse_image(image);rr,rd=b.ungzip(ak[512:]);assert not at and rr==raw and rd==newdt and ar==ram
assert ak[512:-len(rd)]==stream
assert set(diff(header,ah))<=set(range(16,20))|set(range(576,608))
assert ram[:4]==oldram[:4] and ram[8:512]==oldram[8:512]
parsed,extra=b.ungzip(ar[512:]);assert not extra and b.parse_cpio(parsed)==entries
artifacts={'candidate.img':image,'candidate.p10.raw':full,'initramfs.cpio.gz':payload,'ramdisk.wrapped':ram,'Image.gz-dtb':compiled,'resolved.config':config,'runtime.dtb':newdt}
for n,d in artifacts.items():(R/'artifacts'/n).write_bytes(d)
old_inst=(BASE/'source/install.py').read_text();new_inst=old_inst
pre=next(l for l in old_inst.splitlines() if l.startswith('INSTALL_PREIMAGES='))
changes={"IMAGE_SHA='13033865fe5c88952efe2d5e429246a76a08689be604fb89a4776afa990c4ab8'":f"IMAGE_SHA='{b.sha(image)}'",f"FULL_SHA='{current}'":f"FULL_SHA='{b.sha(full)}'",'len(image)==7974912':f'len(image)=={len(image)}',"profile='exact-linux49-runnable-timer-bee07d4f-r1'":f"profile='exact-linux49-direct-clock-syscall-{uuid[:8]}-r1'"}
if current not in pre:changes[pre]=pre[:-1]+f",'{current}')"
for a,z in changes.items():assert new_inst.count(a)==1;new_inst=new_inst.replace(a,z)
restored=new_inst
for a,z in reversed(list(changes.items())):assert restored.count(z)==1;restored=restored.replace(z,a)
assert restored==old_inst
for n in ['execute','Transport','Guard']:assert block(new_inst,n)==block(old_inst,n)
(R/'source/install.py').write_text(new_inst)
(R/'source/install.diff').write_text(''.join(difflib.unified_diff(old_inst.splitlines(True),new_inst.splitlines(True),fromfile='runnable-timer-format-fix/source/install.py',tofile='direct-clock-syscall-control/source/install.py')))
helpers={}
for n in ['bootformat.py','fdt.py','adb','legacy_adb.py']:
 d=(R/'source'/n).read_bytes();assert d==(BASE/'source'/n).read_bytes();helpers[n]=dict(**rec(d),mode=oct(stat.S_IMODE((R/'source'/n).stat().st_mode)))
assert helpers['adb']['mode']=='0o755'
result=dict(status='PACKAGED_ONE_CANDIDATE_NO_PHYSICAL_EXECUTION',pid1_run_uuid=uuid,kernel_entry_uuid_unchanged='23cdb057-295c-4b42-9ade-a4324162ad02',candidate=rec(image),full_p10=rec(full),compiled_Image_gz_dtb=rec(compiled),config=rec(config),compressed_Image=rec(stream),raw_Image=rec(raw),compiled_DTB=rec(compiled_dt),prior_runtime_DTB=rec(dt),runtime_DTB=rec(newdt),init=rec(init),init_source=rec(src),elf=elf,ramdisk=rec(ram),compressed_initramfs=rec(payload),initrd=dict(start='0x44000000',end=hex(newend),payload_bytes=len(payload),wrapper_stripped_bytes=512,existing_guard_end='0x4403f007',existing_guard_safe_superset=newend<=0x4403f007),cmdline=ch['bootargs'].rstrip(b'\0').decode(),preservation=dict(compiled_artifact_byte_identical=True,kernel_gzip_stream_byte_identical=True,raw_Image_byte_identical=True,all_hardware_DT_tokens_byte_identical_to_prior_runtime=True,hardware_properties_equal_compiled_DTB=True,DT_reservations_and_structure_header_byte_identical=True,only_DT_change='chosen/linux,initrd-end',kernel_MTK_wrapper_byte_identical=True,Android_header_changed_offsets=diff(header,ah),ramdisk_MTK_changed_offsets=diff(oldram[:512],ram[:512]),bootargs_and_load_addresses_byte_identical=True,execute_Transport_Guard_byte_identical=True,adapters_and_helpers_byte_identical=helpers),installer=dict(**rec(new_inst.encode()),changes=['image hash','full p10 hash','actual image size','profile','append supplied current preimage'],added_preimage=current,current_pin_supplied_not_freshly_observed=True),limits=['No physical timer/storage/USB claim','Counter interval is not wallclock calibration; cap before one second cannot establish missed alarm','Signal delivery depends on kernel timers/interrupts; Power fallback required','Parent owns installation, physical trial and interpretation; compile VM stopped separately'])
(R/'evidence/packaging-receipt.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ['status','pid1_run_uuid','candidate','full_p10','compressed_initramfs','initrd']},indent=2))
