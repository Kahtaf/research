"""One offline package: replace kernel stream, preserve ENTIRE wrapped ramdisk."""
from pathlib import Path
import ast,difflib,hashlib,json,stat,struct,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[1];B=R.parent/'2026-11-08-asus-pwrap-finite-backstop'
def boundary(event,args):
 if event=='open':assert not any(x in str(args[0]) for x in ['/private/','/device-backup/','root_shell_wifi.py','mtk-su-mirror-b','/dev/'])
 if event.startswith(('subprocess.','socket.')) or event in ['os.system','os.posix_spawn']:raise RuntimeError(event)
sys.addaudithook(boundary);sys.path.insert(0,str(R/'source'));import bootformat as b,fdt
rec=lambda d:dict(bytes=len(d),sha256=b.sha(d))
def block(s,name):
 n=next(n for n in ast.parse(s).body if getattr(n,'name',None)==name);return ''.join(s.splitlines(True)[n.lineno-1:n.end_lineno])
def diff(a,z):
 assert len(a)==len(z);return [i for i,(x,y) in enumerate(zip(a,z)) if x!=y]
with (R/'evidence/package-attempt.json').open('x') as f:json.dump(dict(one_candidate=True,no_device_or_private_inputs=True),f)
old=(B/'artifacts/candidate.img').read_bytes();current='00f163a6a2500ec61b286be7bc6a3fa70f5bb707f2c554a217757649e1f4410e'
assert b.sha(old)=='98abc7acab66442831b2f7a2d92c0224f9e5477cb29e2311d797b69e2ea5dab6'
assert (B/'artifacts/candidate.p10.raw').read_bytes()==old+bytes(b.PARTITION_SIZE-len(old)) and b.sha(old+bytes(b.PARTITION_SIZE-len(old)))==current
header,kernel,ram,tail=b.parse_image(old);assert not tail and b.sha(ram)=='96828e7b595a9ef8687fd5bebfbf0ddbafca31d9e0955041e5f2a0720bd55cb2'
_,runtime=b.ungzip(kernel[512:]);_,nodes,_=fdt.parse(runtime);ch=nodes['/chosen']
compiled=(R/'artifacts/Image.gz-dtb').read_bytes();raw,dt=b.ungzip(compiled);stream=compiled[:-len(dt)]
config=(R/'artifacts/resolved.config').read_bytes();assert config==(B/'artifacts/resolved.config').read_bytes() and b.sha(config)=='708a88175ea777c09410000dfe5cf562ccbf764955eb9deaadda7326d0a966e1'
_,basedt=b.ungzip((B/'artifacts/Image.gz-dtb').read_bytes());assert dt==basedt
_,cn,_=fdt.parse(dt);assert {p:v for p,v in cn.items() if p!='/chosen'}=={p:v for p,v in nodes.items() if p!='/chosen'}
args=b'bootopt=64S3,32N2,64N2 build_version=3 console=null nr_cpus=1 printk.devkmsg=on nohlt'
assert ch['bootargs'].rstrip(b'\0')==header[64:576].rstrip(b'\0')==args and len(args)<92
assert ch['linux,initrd-start']==bytes.fromhex('44000000') and ch['linux,initrd-end']==bytes.fromhex('4403e92a')
cp,extra=b.ungzip(ram[512:]);assert not extra;entries=b.parse_cpio(cp);init=entries['init'][3]
assert b.sha(init)=='9e9db33d3bf4615892ce40fe62bdaeb4f0240e2ebd6dabba81f565cff2ab2a1b'
i=json.loads((R/'evidence/identity.json').read_text());assert i['helper_uuid'].encode() in init and i['control_uuid'].encode() in init
assert i['mode'].encode() in raw and ('ASUS49-ENTRY run='+i['kernel_uuid']).encode() in raw
newkernel=b.wrap(kernel,stream+runtime);image=b.make_image(header,newkernel,ram);full=image+bytes(b.PARTITION_SIZE-len(image))
ah,ak,ar,at=b.parse_image(image);rr,rd=b.ungzip(ak[512:]);assert not at and rr==raw and rd==runtime and ar==ram
assert ak[512:-len(rd)]==stream and b.parse_cpio(b.ungzip(ar[512:])[0])==entries
assert newkernel[:4]==kernel[:4] and newkernel[8:512]==kernel[8:512]
assert set(diff(header,ah))<=set(range(8,12))|set(range(576,608))
assert raw[56:60]==b'ARM\x64';text_offset,image_size=struct.unpack_from('<QQ',raw,8)
ks,ka,rs,ra,ss,sa,ta,page=struct.unpack_from('<8I',ah,8)
end=ra+len(ram)-512;kend=ka+image_size
assert ka==0x40080000 and ra==0x44000000 and text_offset==0x80000 and page==2048 and ss==0 and image_size>=len(raw)
assert kend<=ra and kend<=0x44400000 and end==0x4403e92a<=0x4403f007<0x44400000
for n,d in [('candidate.img',image),('candidate.p10.raw',full),('runtime.dtb',runtime),('ramdisk.wrapped',ram)]:(R/'artifacts'/n).write_bytes(d)
prior=(B/'source/install.py').read_text();s=prior;pre=next(l for l in s.splitlines() if l.startswith('INSTALL_PREIMAGES='));assert current not in pre
changes={"IMAGE_SHA='98abc7acab66442831b2f7a2d92c0224f9e5477cb29e2311d797b69e2ea5dab6'":f"IMAGE_SHA='{b.sha(image)}'",f"FULL_SHA='{current}'":f"FULL_SHA='{b.sha(full)}'",'len(image)==7991296':f'len(image)=={len(image)}',"profile='exact-pwrap-finite-09abbded-v1'":f"profile='exact-battery-uevent-{i['kernel_uuid'][:8]}-v1'",pre:pre[:-1]+f",'{current}')"}
for a,z in changes.items():assert s.count(a)==1;s=s.replace(a,z)
restored=s
for a,z in reversed(list(changes.items())):assert restored.count(z)==1;restored=restored.replace(z,a)
assert restored==prior
for n in ['execute','Transport','Guard']:assert block(prior,n)==block(s,n)
(R/'source/install.py').write_text(s);(R/'source/install.diff').write_text(''.join(difflib.unified_diff(prior.splitlines(True),s.splitlines(True),fromfile='frozen/install.py',tofile='boundary/install.py')))
adapters={}
for n in ['bootformat.py','fdt.py','adb','legacy_adb.py']:
 d=(R/'source'/n).read_bytes();assert d==(B/'source'/n).read_bytes();adapters[n]=dict(**rec(d),mode=oct(stat.S_IMODE((R/'source'/n).stat().st_mode)))
assert adapters['adb']['mode']=='0o755'
result=dict(status='ONE_BATTERY_UEVENT_OMISSION_DIAGNOSTIC_STOP_NO_TRIAL',kernel_uuid=i['kernel_uuid'],mode=i['mode'],format_version=1,max_pid1_writes=768,helper_uuid=i['helper_uuid'],control_uuid=i['control_uuid'],helper_and_control_reused=True,candidate=rec(image),full_p10=rec(full),base_full_p10=current,current_pin_supplied_not_freshly_observed=True,config=rec(config),compiled_Image_gz_dtb=rec(compiled),raw_Image=rec(raw),compiled_DTB=rec(dt),runtime_DTB=rec(runtime),init=rec(init),ramdisk=rec(ram),compressed_initramfs=rec(ram[512:]),initrd=dict(start=hex(ra),end=hex(end),unchanged_entry_guard_end='0x4403f007',remaining_guard_bytes=0x4403f007-end),bootargs=args.decode(),layout=dict(Image_image_size=image_size,loaded_Image_end=hex(kend),no_overlap=True,android_header_changed_offsets=diff(header,ah),kernel_wrapper_changed_offsets=diff(kernel[:512],newkernel[:512])),preservation=dict(entire_wrapped_ramdisk_byte_identical=True,helper_binary_byte_identical=True,config_byte_identical=True,compiled_DT_byte_identical=True,runtime_DT_byte_identical=True,short_bootargs_and_initrd_bounds_unchanged=True,execute_Transport_Guard_byte_identical=True,adapters=adapters),installer=rec(s.encode()))
(R/'evidence/packaging-receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ['status','candidate','full_p10','ramdisk','initrd']},indent=2))
