"""One actual offline recovery package; public pinned inputs only."""
from pathlib import Path
import ast,difflib,hashlib,json,re,stat,struct,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[1];B=R.parent/'2026-11-08-asus-minimal-platform-build-r3'
def boundary(event,args):
 if event=='open' and any(x in str(args[0]) for x in ['/private/','/device-backup/','root_shell_wifi.py','mtk-su-mirror-b','/dev/']):raise RuntimeError('Prohibited reader '+str(args[0]))
 if event.startswith(('subprocess.','socket.')) or event in ['os.system','os.posix_spawn']:raise RuntimeError(event)
sys.addaudithook(boundary);sys.path.insert(0,str(R/'source'));import bootformat as b,fdt
rec=lambda d:dict(bytes=len(d),sha256=b.sha(d))
assert json.loads((R/'evidence/audit-decision.json').read_text())['status']=='ADMITTED_DIAGNOSTIC_ONLY'
linked=json.loads((R/'evidence/linked-verification.json').read_text());build=json.loads((R/'evidence/build-receipt.json').read_text());identity=json.loads((R/'evidence/identity.json').read_text())
assert linked['status']=='LINKED_GUARD_AND_PRESERVATION_CHECKS_PASS' and build['exit']==0
compiled=(R/'artifacts/Image.gz-dtb').read_bytes();raw,dt=b.ungzip(compiled)
assert rec(compiled)==build['artifacts']['arch/arm64/boot/Image.gz-dtb'] and rec(raw)==build['artifacts']['arch/arm64/boot/Image']
assert dt==(R/'artifacts/compiled.dtb').read_bytes()==(B/'artifacts/compiled.dtb').read_bytes()
config=(R/'artifacts/resolved.config').read_bytes();assert config==(B/'artifacts/resolved.config').read_bytes()
init=(R/'artifacts/init').read_bytes();ram=(R/'artifacts/ramdisk.wrapped').read_bytes()
assert init==(B/'artifacts/init').read_bytes() and ram==(B/'artifacts/ramdisk.wrapped').read_bytes()
cp,tail=b.ungzip(ram[512:]);assert not tail;entries=b.parse_cpio(cp);assert entries=={'dev':(0o040755,0,0,b''),'init':(0o100755,0,0,init),'proc':(0o040555,0,0,b'')};b.elf_static(init)
assert ram[512:]==(R/'artifacts/initramfs.cpio.gz').read_bytes() and len(ram)-512==319962
ancestor=(B/'artifacts/candidate.img').read_bytes();assert b.sha(ancestor)=='7ccd7d4554a764d0717c79d30668626c1fbd032218f8598bf7e4a2913bce30a1'
header,old_kernel,old_ram,tail=b.parse_image(ancestor);assert not tail and old_ram==ram
profile=json.loads((B/'source/minimal-profile.json').read_text());args=profile['cmdline'].encode('ascii');assert header[64:576].rstrip(b'\0')==args and len(args)==89
text_offset,image_size=struct.unpack_from('<QQ',raw,8);assert text_offset==0x80000 and image_size>=len(raw)
assert 0x40080000+image_size<=0x44000000 and 0x44000000+len(ram)-512==0x4404e1da<0x44400000
assert identity['entry_tag'].encode() in raw and identity['kernel_run_uuid'].encode() not in init and identity['helper_run_uuid'].encode() in init
panic_prefix='ASUS49-DELAY-BUDGET run='+identity['kernel_run_uuid']+' '
assert panic_prefix.encode() in raw
with (R/'evidence/package-attempt.json').open('x') as f:json.dump(dict(actual_packages=1,kernel_builds=1,helper_builds=0,public_inputs_only=True),f)
image=b.make_image(header,b.wrap(old_kernel,compiled),ram);full=image+bytes(b.PARTITION_SIZE-len(image))
h,k,rd,t=b.parse_image(image);assert not t and k[512:]==compiled and rd==ram
assert all(h[i]==header[i] for i in range(2048) if i not in set(range(8,12))|set(range(16,20))|set(range(576,608)))
assert struct.unpack_from('<8I',h,8)[1:]==(0x40080000,len(ram),0x44000000,0,0x40f00000,0x4e000000,2048)
assert len(full)==16740352 and not any(full[len(image):])
for n,d in [('candidate.img',image),('candidate.p10.raw',full)]:(R/'artifacts'/n).write_bytes(d)
name='exact-global-delay-budget-a4e847a5'
profile.update(profile=name,image=rec(image),full_p10=rec(full),compiled=rec(compiled),raw_Image=rec(raw),Image_image_size=image_size,entry_tag=identity['entry_tag'],kernel_run_uuid=identity['kernel_run_uuid'],helper_run_uuid=identity['helper_run_uuid'],helper_reused_byte_identical=True,panic_prefix=panic_prefix,iteration_budget=1<<24,review='one diagnostic preparation only; no physical GO; iteration budget has no elapsed-time calibration')
del profile['run_uuid']
pb=(json.dumps(profile,indent=2)+'\n').encode();(R/'source/minimal-profile.json').write_bytes(pb)
prior=(B/'source/install.py').read_text();s=prior
replacements={
 "IMAGE_SHA='7ccd7d4554a764d0717c79d30668626c1fbd032218f8598bf7e4a2913bce30a1'":"IMAGE_SHA='"+b.sha(image)+"'",
 "FULL_SHA='9939e802ab349dd01fe5ab9c643f2ce0d3219846e3f54513a9b1e9982146965c'":"FULL_SHA='"+b.sha(full)+"'",
 "MINIMAL_PROFILE_SHA='1192ae278ed208d5ecdb4da1d5f1f2487e71c7591cd101ce5fa28a43a5bac1c9'":"MINIMAL_PROFILE_SHA='"+b.sha(pb)+"'",
 'len(image)==3565568':'len(image)=='+str(len(image)),
 "profile='exact-minimal-platform-a60fca94-r3'":"profile='"+name+"'",
 "profile['profile']=='exact-minimal-platform-a60fca94-r3'":"profile['profile']=='"+name+"'",
 "require(profile['entry_tag'].encode() in raw and profile['run_uuid'].encode() in init,'Entry/helper identity mismatch')":
 "require(profile['kernel_run_uuid']=='"+identity['kernel_run_uuid']+"' and profile['helper_run_uuid']=='"+identity['helper_run_uuid']+"' and profile['helper_reused_byte_identical'] is True,'Kernel/reused-helper identity metadata mismatch')\n require(profile['entry_tag'].encode() in raw and profile['panic_prefix'].encode() in raw and profile['helper_run_uuid'].encode() in init and profile['kernel_run_uuid'].encode() not in init,'Entry/panic/reused-helper identity mismatch')"
}
for a,z in replacements.items():assert s.count(a)==1,(a,s.count(a));s=s.replace(a,z)
line=next(l for l in s.splitlines() if l.startswith('INSTALL_PREIMAGES='));current='9939e802ab349dd01fe5ab9c643f2ce0d3219846e3f54513a9b1e9982146965c';assert current not in line
s=s.replace(line,line[:-1]+",'"+current+"')")
def block(text,name):
 n=next(n for n in ast.parse(text).body if getattr(n,'name',None)==name);return ''.join(text.splitlines(True)[n.lineno-1:n.end_lineno])
unchanged={}
for n in ['execute','Transport','Guard']:
 assert block(prior,n)==block(s,n);unchanged[n]=b.sha(block(s,n).encode())
for n in ['adb','legacy_adb.py','bootformat.py','fdt.py','ram_pid1.c','run_identity.h']:assert (R/'source'/n).read_bytes()==(B/'source'/n).read_bytes()
assert stat.S_IMODE((R/'source/adb').stat().st_mode)==0o755
(R/'source/install.py').write_text(s);(R/'source/install.diff').write_text(''.join(difflib.unified_diff(prior.splitlines(True),s.splitlines(True),fromfile='r3/install.py',tofile='delay-budget/install.py')))
result=dict(status='ONE_DIAGNOSTIC_CANDIDATE_PACKAGED',candidate=rec(image),full_p10=rec(full),compiled=rec(compiled),raw_Image=rec(raw),config=rec(config),DT=rec(dt),helper=rec(init),ramdisk=rec(ram),kernel_run_uuid=identity['kernel_run_uuid'],helper_run_uuid=identity['helper_run_uuid'],helper_rebuilt=False,common_mutating_blocks_unchanged=unchanged,adapters_unchanged=True,only_appended_preimage=current,current_preimage_owner_supplied_not_observed=True,installer=rec(s.encode()),profile=rec(pb),Image_image_size=image_size,loaded_Image_end=hex(0x40080000+image_size),recovery_only=True,physical_GO=False)
(R/'evidence/packaging-receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
