"""Offline provenance and final construction verification; public fixed inputs only."""
from pathlib import Path
import os,resource,json,hashlib,subprocess,shutil,struct,zlib,re,sys
R=Path(__file__).resolve().parents[1];A=R/'artifacts';O=Path('/srv/android/2026-11-06-asus-ram-original-recovery-restorer');T=Path('/srv/android/asus-target-rescue/artifacts/tools-delivery')
assert str(R)=='/srv/android/2026-11-06-asus-stock-only-ram-rescue-build'
os.chdir(R);os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
sha=lambda x:hashlib.sha256(x).hexdigest()
pins=json.loads((R/'inputs/remote-original-pins.json').read_text())
for rel,pin in pins.items():assert sha((O/rel).read_bytes())==pin,rel
(R/'evidence/remote-original-unchanged.json').write_text(json.dumps(dict(passed=True,files=len(pins),pins=pins,old_zero_record_image_sha256=pins['artifacts/candidate/UNARMED.img'],old_full_p10_sha256=pins['artifacts/candidate/UNARMED.p10.raw']),indent=2)+'\n')
assert sha((R/'source/host.py').read_bytes())=='2d6acd11f5b46585bec820188463e4ecb863ec19a6f106a83320f14c24c479d9'
source_delta={p.name:dict(before=sha((O/'source'/p.name).read_bytes()),after=sha(p.read_bytes())) for p in (R/'source').iterdir() if p.is_file()}
changed=[n for n,v in source_delta.items() if v['before']!=v['after']]
assert set(changed)=={'host.py','core_binding.h','generated_host_binding.py'},changed
for n,pin in {'restore-sepolicy':'16f6ce7f25c1b56aba9e4179573c49a6c55f9b9fe3f18336029f6d83b5b4b2c2','file_contexts.bin':'d82c9ca28d1d9017aea5f58d1cb9b46f6122ef22953ab32b7b4a3a8ccd07186c','os-rescue':'606b659f213e1acb80de469bc8273203ddc60cc0b2ca76d943cccfe5ebc8ec63','original-stock.manifest':'605cdec038dafe3dddabfe92b8bd6cd189734f740230dfc362d02a43421e4e47','original-recovery.payload':'902b2f06a01cca574b4aa374e67c4e7f8f0ed53f6e6a55017b6d96351f0f1f20'}.items():assert sha((A/n).read_bytes())==pin,(n,pin)
(R/'evidence/source-delta.json').write_text(json.dumps(dict(passed=True,changed=changed,files=source_delta,production_target_sources_unchanged=True,policy_source_unchanged=True),indent=2)+'\n')
sys.path.insert(0,str(R/'source'));import host
contract=json.loads((A/'candidate/session-contract.UNAPPROVED.json').read_text())
assert host.ARMED is False and host.TIMING_QUALIFIED is False and host.PRIOR_SHA==contract['p10_full_sha256'] and host.HELPER_SHA==contract['helper_sha256']
assert contract['manifest_records']==2 and contract['execute_approved'] is False and contract['physical_GO'] is False and contract['timing_qualified'] is False
# Normalize actual assembled bytes independently of the image writer.
img=(A/'candidate/UNAPPROVED-STOCK-ONLY.img').read_bytes();raw=(A/'candidate/UNAPPROVED-STOCK-ONLY.p10.raw').read_bytes()
ks,ka,rs,ra,ss,sa,tags,page=struct.unpack_from('<8I',img,8);ro=page+(ks+page-1)//page*page
kernel=img[page:page+ks];rd=img[ro:ro+rs]
z=zlib.decompressobj(31);z.decompress(rd[512:]);used=len(rd)-512-len(z.unused_data);offset=(used+3)//4*4
h=bytearray(img[:page]);h[16:20]=bytes(4);h[576:608]=bytes(32);w=bytearray(rd[:512]);w[4:8]=bytes(4)
text=(R/'source/core_binding.h').read_text()
for name,data in [('core_header_sha',h),('core_wrapper_sha',w),('core_kernel_sha',kernel),('core_gzip_sha',rd[512:512+offset])]:
 match=re.search(name+r'\[32\]=\{([^}]+)\}',text);assert match
 assert bytes(int(x,16) for x in match[1].split(','))==hashlib.sha256(data).digest(),name
assert int(re.search(r'CORE_KERNEL_BYTES (\d+)U',text)[1])==ks
assert int(re.search(r'CORE_GZIP_BYTES (\d+)U',text)[1])==offset
base=bytearray((A/'base-header').read_bytes());base[16:20]=bytes(4);base[576:608]=bytes(32);assert h==base
assert raw==img+bytes(16740352-len(img)) and sha(raw)==host.PRIOR_SHA
# These are preserved firmware header addresses and the existing 4 MiB ramdisk cap,
# not a new physical memory-placement qualification.
assert rs-512<=0x400000 and len(raw)==32696*512
m=(A/'original-stock.manifest').read_bytes();rows=[];at=112
for i in range(2):
 role,part,size=struct.unpack_from('<IIQ',m,at);count=struct.unpack_from('<I',m,at+48)[0]
 rows.append(dict(role=['original_SYSTEM','original_BOOT'][i],role_index=role,partition=part,bytes=size,sha256=m[at+16:at+48].hex(),chunks=count));at+=52+32*count
assert at==len(m)
geometry=dict(kernel_address=ka,ramdisk_address=ra,second_address=sa,tags_address=tags,page_bytes=page,kernel_wrapped_bytes=ks,ramdisk_wrapped_bytes=rs,ramdisk_payload_bytes=rs-512,reservation_bytes=0x400000,reservation_headroom=0x400000-(rs-512),image_bytes=len(img),partition_bytes=len(raw),partition_headroom=len(raw)-len(img),recovery=dict(major=179,minor=10,start_sector=160184,sectors=32696,bytes=16740352),original_roles=rows,manifest_sha256=sha(m),cid_sha256=m[16:48].hex(),primary_gpt_sha256=m[48:80].hex(),backup_gpt_sha256=m[80:112].hex(),physical_validation=False)
(R/'evidence/bindings-and-geometry.json').write_text(json.dumps(dict(passed=True,normalized_bindings_match=True,external_host_pins_match=True,original_header_addresses_preserved=True,**geometry),indent=2)+'\n')
# Fresh compiler, actual linker/static library, context tool, and fixture-kernel pins.
tools={}
for command in ['aarch64-linux-gnu-gcc','gcc','aarch64-linux-gnu-ld','ld','qemu-system-aarch64','python3']:
 p=Path(shutil.which(command)).resolve();tools[command]=dict(path=str(p),sha256=sha(p.read_bytes()),version=subprocess.check_output([command,'--version'],text=True).splitlines()[0])
for command in ['aarch64-linux-gnu-gcc','gcc']:
 for name in ['cc1','libc.a','libgcc.a','crt1.o','crti.o','crtn.o']:
  p=Path(subprocess.check_output([command,('-print-prog-name=' if name=='cc1' else '-print-file-name=')+name],text=True).strip()).resolve();assert p.is_file();tools[command+':'+name]=dict(path=str(p),sha256=sha(p.read_bytes()))
for p in [T/'libsepol/src/libsepol.a',T/'sefcontext_compile',Path('/srv/android/asus-target-rescue/build/compat-out/arch/arm64/boot/Image')]+sorted((T/'libsepol/include').rglob('*.h')):
 tools[str(p)]=dict(path=str(p),sha256=sha(p.read_bytes()))
(R/'evidence/toolchain.json').write_text(json.dumps(tools,indent=2)+'\n')
sourcepins={str(p.relative_to(R)):sha(p.read_bytes()) for d in ['source','scripts','tests','inputs'] for p in (R/d).rglob('*') if p.is_file() and '__pycache__' not in str(p)}
(R/'SOURCE_PINS.json').write_text(json.dumps(sourcepins,indent=2)+'\n')
artifacts={str(p.relative_to(R)):dict(bytes=p.stat().st_size,sha256=sha(p.read_bytes())) for p in A.rglob('*') if p.is_file() and 'reproduction' not in p.relative_to(A).parts}
(R/'ARTIFACTS.json').write_text(json.dumps(artifacts,indent=2)+'\n')
print('POSTFLIGHT_PINS_GEOMETRY_ORIGINALS_UNCHANGED_PASS')
