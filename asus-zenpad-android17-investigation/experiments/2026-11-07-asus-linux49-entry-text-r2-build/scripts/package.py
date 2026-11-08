"""One local packaging/preservation unit. No private inputs or device access."""
from pathlib import Path
import sys,struct,json,hashlib,ast,difflib
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[1];W=R.parent
BASE=W/'2026-11-07-asus-linux49-failure-log-package'
CURRENT='d6949069eaa498fcfbc27be707d01dffd7099992c5eb71e2c7c3926639851355'
assert len(CURRENT)==64 and all(c in '0123456789abcdef' for c in CURRENT)
def boundary(event,args):
 if event=='open':
  p=str(args[0]);assert not any(x in p for x in ['/private/','/device-backup/','root_shell_wifi.py','mtk-su-mirror-b','/dev/']),p
 if event.startswith(('subprocess.','socket.')) or event in ['os.system','os.posix_spawn']:raise RuntimeError('No processes/network in package unit: '+event)
sys.addaudithook(boundary)
sys.path.insert(0,str(R/'source'))
import bootformat as b,fdt
rec=lambda d:dict(bytes=len(d),sha256=b.sha(d))
def block(text,name):
 n=next(n for n in ast.parse(text).body if getattr(n,'name',None)==name)
 return ''.join(text.splitlines(True)[n.lineno-1:n.end_lineno])
def diff(a,z):
 assert len(a)==len(z);return [i for i,(x,y) in enumerate(zip(a,z)) if x!=y]
assert not (R/'evidence/package-attempt.json').exists(),'One package unit only'
(R/'evidence/package-attempt.json').write_text(json.dumps(dict(mode='ONE_LOCAL_PACKAGE_PRESERVATION_UNIT',private=False,device=False))+'\n')
old=(BASE/'artifacts/candidate.img').read_bytes();assert b.sha(old)=='cc367b543eebea476b15a9033648c9547e48c7ac02d8c42856b372623bffb265'
oldfull=(BASE/'artifacts/candidate.p10.raw').read_bytes();assert b.sha(oldfull)=='0b1a3c45751d688ba304743dc74e73f7030586c6fafece32eedf0da39c86455d'
header,kernel,ram,tail=b.parse_image(old);assert not tail
compiled=(R/'artifacts/Image.gz-dtb').read_bytes();config=(R/'artifacts/resolved.config').read_bytes()
assert b.sha(config)=='708a88175ea777c09410000dfe5cf562ccbf764955eb9deaadda7326d0a966e1'
raw,dt=b.ungzip(compiled);oldraw,olddt=b.ungzip(kernel[512:]);baseline=(BASE/'artifacts/Image.gz-dtb').read_bytes();_,baselinedt=b.ungzip(baseline)
assert b.sha(baseline)=='a49b87313d35d803e3ffaa2be2c60a3c678ccbc46efd5831651d2bd44ae4ee03'
assert dt==baselinedt, 'Compiled full DT must remain byte-identical'
expected=(R/'source/expected-runtime.dtb').read_bytes();assert olddt==expected
_,cn,_=fdt.parse(dt);_,pn,_=fdt.parse(expected)
assert {p:v for p,v in cn.items() if p!='/chosen'}=={p:v for p,v in pn.items() if p!='/chosen'}
assert pn['/chosen']['linux,initrd-start']==bytes.fromhex('44000000')
assert pn['/chosen']['linux,initrd-end']==(0x44000000+len(ram)-512).to_bytes(4,'big')
assert pn['/chosen']['bootargs'].rstrip(b'\0')==header[64:576].rstrip(b'\0')
stream=compiled[:-len(dt)]
newkernel=b.wrap(kernel,stream+expected)
assert newkernel[:4]==kernel[:4] and newkernel[8:512]==kernel[8:512]
assert struct.unpack_from('<I',newkernel,4)[0]==len(newkernel)-512
image=b.make_image(header,newkernel,ram);full=image+bytes(b.PARTITION_SIZE-len(image))
(R/'artifacts/candidate.img').write_bytes(image);(R/'artifacts/candidate.p10.raw').write_bytes(full)
ah,ak,ar,at=b.parse_image(image);rr,rd=b.ungzip(ak[512:]);assert ar==ram and not at and rr==raw and rd==expected
assert set(diff(header,ah))<=set(range(8,12))|set(range(576,608))
assert ram==(BASE/'artifacts/ramdisk.wrapped').read_bytes()
cp,extra=b.ungzip(ram[512:]);entries=b.parse_cpio(cp);assert not extra
init=entries['init'][3];assert init==(BASE/'artifacts/init').read_bytes()
assert b.sha(init)=='f410df21053fcac5f418c7d64749f19bae7921e5cc13f5c37fe5f9e99268752d'
assert b'alarm(60)' in (BASE/'source/init.c').read_bytes()
old_inst=(BASE/'source/install.py').read_text();new_inst=old_inst
preimages=next(l for l in old_inst.splitlines() if l.startswith('INSTALL_PREIMAGES='));assert CURRENT not in preimages
changes={"IMAGE_SHA='cc367b543eebea476b15a9033648c9547e48c7ac02d8c42856b372623bffb265'":f"IMAGE_SHA='{b.sha(image)}'","FULL_SHA='0b1a3c45751d688ba304743dc74e73f7030586c6fafece32eedf0da39c86455d'":f"FULL_SHA='{b.sha(full)}'",'len(image)==7974912':f'len(image)=={len(image)}',"profile='exact-linux49-unchanged-kernel-configfs-failure-log-r1'":"profile='exact-linux49-entry-text-checkpoint-95c88f32-r2'",preimages:preimages[:-1]+f",'{CURRENT}')"}
for a,z in changes.items():assert new_inst.count(a)==1;new_inst=new_inst.replace(a,z)
restored=new_inst
for a,z in reversed(list(changes.items())):assert restored.count(z)==1;restored=restored.replace(z,a)
assert restored==old_inst
for name in ['execute','Transport','Guard']:assert block(new_inst,name)==block(old_inst,name)
(R/'source/install.py').write_text(new_inst);(R/'source/install.diff').write_text(''.join(difflib.unified_diff(old_inst.splitlines(True),new_inst.splitlines(True),fromfile='failure-log-package/source/install.py',tofile='entry-text/source/install.py')))
helpers={}
for name in ['bootformat.py','fdt.py','adb','legacy_adb.py']:
 a=(R/'source'/name).read_bytes();assert a==(BASE/'source'/name).read_bytes();helpers[name]=rec(a)
identity=json.loads((R/'evidence/identity.json').read_text());linked=json.loads((R/'evidence/linked-entry.json').read_text());assert linked['tag']==identity['tag']
assert identity['tag'].encode() in raw
result=dict(status='ONE_ENTRY_TEXT_CANDIDATE_PACKAGED_NO_PHYSICAL_OR_OS_ADMISSION',run_uuid=identity['run_uuid'],entry_tag=identity['tag'],candidate=rec(image),full_p10=rec(full),compiled_Image_gz_dtb=rec(compiled),config=rec(config),raw_Image=rec(raw),compressed_Image=rec(stream),compiled_DTB=rec(dt),packaged_reference_DTB=rec(expected),base_candidate=rec(old),base_full_p10=rec(oldfull),wrapped_ramdisk=rec(ram),init=rec(init),init_source=rec((BASE/'source/init.c').read_bytes()),initrd=dict(start='0x44000000',end='0x4403f007',payload_bytes=len(ram)-512,wrapper_excluded=512),cmdline=pn['/chosen']['bootargs'].rstrip(b'\0').decode(),preservation=dict(full_config_byte_identical=True,compiled_full_DTB_byte_identical=True,packaged_full_DTB_byte_identical=True,all_hardware_and_reservation_contracts_unchanged=True,ramdisk_init_bootargs_MTK_and_Android_load_addresses_unchanged=True,reporter_60_second_reboot_and_power_fallback_unchanged=True,execute_Transport_Guard_and_adapters_byte_identical=True,helpers=helpers),delta=dict(Android_header_offsets=diff(header,ah),kernel_wrapper_offsets=diff(kernel[:512],newkernel[:512]),installer_only_changes=['actual image pin','actual full p10 pin','actual image size','profile','append current preimage'],added_preimage=CURRENT,supplied_current_not_freshly_observed=True),installer=rec(new_inst.encode()),limits=['Bounded structural runtime DT admission; absent marker remains UNKNOWN','Host and linked checks are not physical execution/retention proof','Fresh physical run UUID tag required; absent text is UNKNOWN','No final OS admission; parent owns one trial and VM stop'])
(R/'evidence/packaging-receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ['status','run_uuid','candidate','full_p10','compiled_Image_gz_dtb','config']},indent=2))
