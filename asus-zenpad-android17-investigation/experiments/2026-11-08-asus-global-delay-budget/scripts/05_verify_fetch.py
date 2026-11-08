from pathlib import Path
import base64,gzip,hashlib,json,re,struct,subprocess
R=Path('/srv/android/asus-global-delay-budget-20261108');B=Path('/srv/android/asus-minimal-platform-build-r3-20261108');K=R/'kernel';O=R/'out';E=R/'evidence'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert json.loads((E/'kernel-status.json').read_text())['exit']==0
assert sha(O/'.config')=='01d6729f825798899e21192e6c33f96a80b47ccbedd5dc6cab10f78c1f9c7f31'
assert sha(O/'arch/arm64/boot/dts/mediatek/asus-p00a.dtb')=='156e92ec5d4f5c4bd20169128c8aed0a89b43636d945d648392aaaec8b9bf82e'
prep=json.loads((E/'preparation.json').read_text())
for n,v in prep['source_changes'].items():assert sha(K/n)==v['postimage'] and sha(B/'kernel'/n)==v['preimage']
nm=subprocess.check_output(['aarch64-linux-gnu-nm','-an',str(O/'vmlinux')],text=True);symbols={l.split()[2]:int(l.split()[0],16) for l in nm.splitlines() if len(l.split())==3}
files={};ds={}
for name in ['__delay','__const_udelay','__udelay','__ndelay','panic','arch_counter_get_cntvct','asus_entry_text_begin']:
 if name not in symbols:continue
 d=subprocess.check_output(['aarch64-linux-gnu-objdump','-d','--disassemble='+name,str(O/'vmlinux')],text=True);ds[name]=d
 if name!='asus_entry_text_begin':
  p=E/(name+'.disasm');p.write_text(d)
d=ds['__delay'];assert '<dump_stack>' in d and '<panic>' in d and '\tyield' in d and 'cntvct_el0' in d.lower()
assert 'cntpct_el0' not in d.lower() and 'cntfrq_el0' not in d.lower()
assert sum('mrs' in l and 'cntvct_el0' in l.lower() for l in d.splitlines())==2
assert sum('\tisb' in l for l in d.splitlines())==2
assert sum('\tblr' in l for l in d.splitlines())==2
# Extract the actual linked function bytes from its ELF load segment.
sized=subprocess.check_output(['aarch64-linux-gnu-nm','-S',str(O/'vmlinux')],text=True)
row=next(l.split() for l in sized.splitlines() if l.split()[-1]=='__delay');addr,size=int(row[0],16),int(row[1],16)
v=(O/'vmlinux').read_bytes();phoff=struct.unpack_from('<Q',v,32)[0];ents,num=struct.unpack_from('<HH',v,54)
seg=next(x for i in range(num) if (x:=struct.unpack_from('<IIQQQQQQ',v,phoff+i*ents))[0]==1 and x[3]<=addr and addr+size<=x[3]+x[5])
code=v[seg[2]+addr-seg[3]:seg[2]+addr-seg[3]+size];assert len(code)==size
(E/'__delay.linked.bin').write_bytes(code)
raw=(O/'arch/arm64/boot/Image').read_bytes();entry=(K/'arch/arm64/kernel/asus_entry_tag.h').read_text();tag=json.loads(entry.split(' ',2)[2].split('\n')[0]).encode()
assert raw.count(tag)==2 and b'ASUS49-DELAY-BUDGET run=a4e847a5-f502-4562-8e6a-c9a358e3f22f ' in raw
assert b'ASUS49-ENTRY run=a60fca94-e760-4ce5-a790-5c9a818ce406 ' not in raw
assert (O/'include/generated/utsrelease.h').read_text().split('"')[1]=='4.9.337-asus-p00a-experimental-minplat'
text_offset,image_size=struct.unpack_from('<QQ',raw,8);assert raw[56:60]==b'ARM\x64' and text_offset==0x80000 and image_size>=len(raw) and 0x40080000+image_size<=0x44000000
# Entry commit path and original handoff remain present at linked symbol boundaries.
read=lambda a,z:raw[a-symbols['_text']:z-symbols['_text']]
assert symbols['stext']==symbols['asus_entry_text_begin']
assert read(symbols['asus_entry_tag'],symbols['asus_entry_tag_end'])==tag
assert read(symbols['entry_marker'],symbols['entry_marker']+len(tag))==tag
assert read(symbols['asus_entry_text_commit'],symbols['asus_entry_text_commit']+8)==bytes.fromhex('913800b99f3f03d5')
end=symbols['asus_entry_text_end']
for j,target in enumerate(['preserve_boot_args','el2_setup']):
 at=end+4*j;word=struct.unpack('<I',read(at,at+4))[0];assert word&0xfc000000==0x94000000
 imm=word&0x3ffffff;imm=imm-(1<<26) if imm&(1<<25) else imm
 assert at+4*imm==symbols[target]
(E/'entry.disasm').write_text(subprocess.check_output(['aarch64-linux-gnu-objdump','-d','--start-address='+hex(symbols['stext']),'--stop-address='+hex(end+12),str(O/'vmlinux')],text=True))
# Disclose fresh warning differences; do not repair/retry a build.
def warnings(p):
 return sorted(set(re.sub(r':\d+(?::\d+)?(?=:)',':LINE',re.sub(r'/srv/android/[^\s:]+/(kernel|out)/',r'\1/',l)) for l in p.read_text(errors='replace').splitlines() if 'warning:' in l))
new=sorted(set(warnings(E/'kernel-compile.log'))-set(warnings(B/'evidence/kernel-compile.log')))
rec=dict(status='LINKED_GUARD_AND_PRESERVATION_CHECKS_PASS',config_sha256=sha(O/'.config'),dt_sha256=sha(O/'arch/arm64/boot/dts/mediatek/asus-p00a.dtb'),source_changes=prep['source_changes'],linked_elf_sha256=sha(O/'vmlinux'),delay_address=hex(addr),delay_bytes=size,delay_code_sha256=hashlib.sha256(code).hexdigest(),original_route_mrs_sites=2,original_route_indirect_workaround_sites=2,original_isb_sites=2,yield_present=True,dump_stack_and_terminal_panic=True,Image_image_size=image_size,loaded_end=hex(0x40080000+image_size),entry_tag=tag.decode(),new_warning_signatures=new,physical_execution=False)
(E/'linked-verification.json').write_text(json.dumps(rec,indent=2)+'\n')
smap=(O/'System.map').read_bytes();(E/'System.map-receipt.json').write_text(json.dumps(dict(bytes=len(smap),sha256=hashlib.sha256(smap).hexdigest()),indent=2)+'\n')
paths={'artifacts/Image.gz-dtb':O/'arch/arm64/boot/Image.gz-dtb','artifacts/compiled.dtb':O/'arch/arm64/boot/dts/mediatek/asus-p00a.dtb','artifacts/resolved.config':O/'.config','artifacts/System.map':O/'System.map','artifacts/delay.o':O/'arch/arm64/lib/delay.o','source/final/arch/arm64/lib/delay.c':K/'arch/arm64/lib/delay.c','source/final/arch/arm64/kernel/asus_entry_tag.h':K/'arch/arm64/kernel/asus_entry_tag.h'}
for n in ['utsrelease.h','compile.h']:paths['evidence/'+n]=O/'include/generated'/n
for p in E.glob('*'):
 if p.is_file():paths['evidence/'+p.name]=p
for name,p in paths.items():
 b=p.read_bytes();files[name]=dict(data=base64.b64encode(b).decode(),sha256=hashlib.sha256(b).hexdigest())
print(json.dumps(dict(files=files,verification=rec)))
