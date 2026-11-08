"""One actual linked writer/snapshot/readback ABI replay and public packaging check."""
from pathlib import Path
import sys,struct,json,ast,difflib,gzip,re,collections
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[1];W=R.parent
assert not (R/'evidence/packaging-receipt.json').exists(),'One candidate only'
def boundary(event,args):
 if event=='open':assert not any(x in str(args[0]) for x in ('/private/','/device-backup/','root_shell_wifi.py','mtk-su-mirror-b','/dev/'))
 if event.startswith(('socket.','subprocess.')) or event in ('os.system','os.posix_spawn'):raise RuntimeError(event)
sys.addaudithook(boundary)
from elftools.elf.elffile import ELFFile
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_ARM
from unicorn import Uc,UC_ARCH_ARM64,UC_MODE_ARM,UC_HOOK_CODE,UC_HOOK_MEM_WRITE
from unicorn.arm64_const import *
sys.path.insert(0,str(W/'2026-11-07-asus-stock-kernel-version-control/source'))
import bootformat as b,kallsyms
sys.path.insert(0,str(W/'2026-11-06-asus-full-boot-lk-contract/scripts'))
import fdt,lk_contract
p=json.loads((R/'evidence/preparation.json').read_text());base=int(p['base'],16);slot=int(p['slot'],16);END=int(p['end'],16);APP=int(p['bss_start'],16);phys=lambda a:a-base+0x40080000
blob=(W/'2026-11-07-asus-stock-legacy-ram-usb-reporter/artifacts/candidate.img').read_bytes();header,kernel,ramdisk,trailing=b.parse_image(blob);raw,dt=b.ungzip(kernel[512:]);ss,s,_,aa=kallsyms.decode(raw)
assert b.sha(blob)=='dc0b98e66798e3abc019f454921b1c84ff3ce58e356e26d0785e05b7714d3427' and b.sha(raw)=='db90ee7fff379f35ac2b0aafb11a6abee7b2c283b57d352c40ae7c6d7c35eb2a'
with (R/'qa/control.elf').open('rb') as file:
 e=ELFFile(file);sections={n:(e.get_section_by_name(n)['sh_addr'],e.get_section_by_name(n).data()) for n in ('.entry','.init.rodata','.readback')};sy={x.name:x['st_value'] for x in e.get_section_by_name('.symtab').iter_symbols() if x.name}
 assert not any(x['sh_type'] in ('SHT_REL','SHT_RELA') for x in e.iter_sections())
assert sections['.entry'][0]==APP and sections['.readback'][0]==slot
code=sections['.entry'][1];tag=sections['.init.rodata'][1][sy['asus_entry_tag']-sections['.init.rodata'][0]:sy['asus_entry_tag_end']-sections['.init.rodata'][0]];wrapper=sections['.readback'][1];assert tag==p['tag'].encode() and len(tag)==p['tag_bytes']
append_end=max(a+len(v) for a,v in sections.values() if a>=APP)
assert append_end<int(p['bss_stop'],16)<END and append_end-APP<0x2000
assert phys(append_end)<0x41c80000<0x41e00000 and phys(END)<0x44000000
cs=Cs(CS_ARCH_ARM64,CS_MODE_ARM)
def listing(value,address):return ''.join(f'{i.address:#x} {i.bytes.hex()} {i.mnemonic} {i.op_str}\n' for i in cs.disasm(value,address))
entry=list(cs.disasm(code,APP));writer=[i for i in entry if i.address<sy['asus_entry_text_end']]
for i in writer:
 assert not re.search(r'\b(?:sp|[xw](?:[1-3]|1[89]|2[0-9]|30))\b',i.op_str)
 assert i.mnemonic not in ('bl','blr','ret','stp','ldp')
 assert not re.match(r'[xw]0\b',i.op_str) or i.mnemonic in ('cmp','tst')
assert entry[-1].mnemonic=='b' and entry[-1].op_str==f'#{base+64:#x}'
assert code[sy['asus_entry_text_commit']-APP:sy['asus_entry_text_commit']-APP+8]==bytes.fromhex('913800b99f3f03d5')
# Assemble actual candidate raw bytes before the one replay; no fixture DT is packaged.
def branch(pc,target,link=False):
 d=target-pc;assert d%4==0 and -(1<<27)<=d<(1<<27)
 return struct.pack('<I',(0x94000000 if link else 0x14000000)|((d//4)&0x3ffffff))
clear=0xffffffc000f41564
assert raw[:4]==bytes.fromhex('10000014') and raw[clear-base:clear-base+4]==bytes.fromhex('4924c597')
new=bytearray(raw)+bytes(append_end-(base+len(raw)))
patches=[(base,raw[:4],branch(base,APP),'entry B'),(clear,raw[clear-base:clear-base+4],branch(clear,slot,True),'pre-clear BL'),(slot,raw[slot-base:slot-base+len(wrapper)],wrapper,'mapped proc diagnostic slot')]
for a,old,v,why in patches:assert new[a-base:a-base+len(v)]==old;new[a-base:a-base+len(v)]=v
for a,v in sections.values():
 if a>=APP:new[a-base:a-base+len(v)]=v
allowed={i for a,o,v,why in patches for i in range(a-base,a-base+len(v))};changed={i for i in range(len(raw)) if raw[i]!=new[i]};assert changed<=allowed
# Execute actual physical entry/header branch with only observed memory-reg overlay.
u=Uc(UC_ARCH_ARM64,UC_MODE_ARM);u.mem_map(0x40080000,(len(new)+4095)&~4095);u.mem_write(0x40080000,bytes(new))
FDT=0x47000000;RET=0x44400000;fixture=(R/'qa/fixture-runtime-memory.dtb').read_bytes();u.mem_map(FDT,(len(fixture)+4095)&~4095);u.mem_write(FDT,fixture)
u.mem_map(RET,0x80000);incoming=bytearray(b'P'*0x80000);struct.pack_into('<7I',incoming,0,0x43474244,64,192,128,320,576,256);struct.pack_into('<6I',incoming,0x28,*([0xffffffff]*6));u.mem_write(RET,bytes(incoming))
regs=[UC_ARM64_REG_X0+i for i in range(29)]+[UC_ARM64_REG_X29,UC_ARM64_REG_X30]
for n,r in enumerate(regs):u.reg_write(r,FDT if n==0 else 0x123400000000+n)
u.reg_write(UC_ARM64_REG_SP,0x76543000);writes=[];steps=0
mrs={phys(i.address):i for i in writer if i.mnemonic=='mrs'}
def hook(uc,a,size,data):
 global steps
 steps+=1
 if a in mrs:uc.reg_write(UC_ARM64_REG_X4,4 if 'currentel' in mrs[a].op_str.lower() else 0);uc.reg_write(UC_ARM64_REG_PC,a+4)
def store(uc,access,a,size,v,data):writes.append((a,size,v))
hook1=u.hook_add(UC_HOOK_CODE,hook);hook2=u.hook_add(UC_HOOK_MEM_WRITE,store)
u.emu_start(0x40080000,0x40080040,count=2000000);assert u.reg_read(UC_ARM64_REG_PC)==0x40080040
for n in (0,1,2,3,*range(18,31)):assert u.reg_read(regs[n])==(FDT if n==0 else 0x123400000000+n)
assert u.reg_read(UC_ARM64_REG_SP)==0x76543000
stored=bytes(u.mem_read(RET,0x80000));off_console,count=struct.unpack_from('<I',stored,0x30)[0],struct.unpack_from('<I',stored,0x38)[0]
assert count==len(tag) and stored[off_console:off_console+count]==tag
assert all(RET<=a and a+sz<=RET+0x80000 for a,sz,v in writes)
assert stored[64:832]==incoming[64:832] # both complete platform pairs
u.hook_del(hook1);u.hook_del(hook2)
# Execute stock's actual snapshot-copy loop and current geometry/clear sequence.
# Allocations, mapped pointer and incoming validated OEM geometry are explicit fixtures.
u.mem_map(base,(END-base+4095)&~4095);u.mem_write(base,bytes(new))
CURRENT=0x60000000;SAVED=0x61000000;STACK=0x62000000
for a,z in [(CURRENT,0x80000),(SAVED,0x80000),(STACK,0x10000)]:u.mem_map(a,z)
u.mem_write(CURRENT,stored);u.mem_write(0xffffffc001278568,struct.pack('<Q',SAVED));u.mem_write(0xffffffc001278560,struct.pack('<Q',CURRENT))
u.reg_write(UC_ARM64_REG_X19,CURRENT);u.reg_write(UC_ARM64_REG_X20,0xffffffc001278000);u.reg_write(UC_ARM64_REG_X0,SAVED);u.reg_write(UC_ARM64_REG_X1,0);u.reg_write(UC_ARM64_REG_SP,STACK+0x8000)
for n in range(21,31):u.reg_write(regs[n],0x112233000000+n)
u.reg_write(UC_ARM64_REG_X29,STACK+0x8000)
callee_before={n:u.reg_read(regs[n]) for n in range(19,31)};sp_before=u.reg_read(UC_ARM64_REG_SP)
observed=[];clear_args=[];at_call={};post_clear={}
def late(uc,a,size,data):
 if a==clear:
  at_call.update({n:uc.reg_read(regs[n]) for n in range(19,31)});at_call['sp']=uc.reg_read(UC_ARM64_REG_SP);at_call['args']=[uc.reg_read(regs[n]) for n in range(3)]
 if a==s['printk']:
  fmt=bytes(uc.mem_read(uc.reg_read(UC_ARM64_REG_X0),7));precision=uc.reg_read(UC_ARM64_REG_W1);ptr=uc.reg_read(UC_ARM64_REG_X2)
  assert fmt==b'\x011%.*s\0' and precision==len(tag) and ptr==SAVED+off_console
  actual=bytes(uc.mem_read(ptr,precision));assert actual==tag;observed.append(dict(pointer=hex(ptr),precision=precision,text=actual.decode(),source='actual snapshot of writer stores, not constant'))
  # ABI-adversarial printk substitute: corrupt every caller-saved register.
  lr=uc.reg_read(UC_ARM64_REG_X30)
  for n in range(19):uc.reg_write(regs[n],0xc0de0000+n)
  uc.reg_write(UC_ARM64_REG_PC,lr)
 if a==s['__memset_io']:
  args=[uc.reg_read(regs[n]) for n in range(3)];assert args==at_call['args'];clear_args.append(args)
  # Emulate the unchanged original clear's ordinary contract; no retained text substitute.
  uc.mem_write(args[0],bytes([args[1]&255])*args[2]);lr=uc.reg_read(UC_ARM64_REG_X30)
  for n in range(19):uc.reg_write(regs[n],0xface0000+n)
  uc.reg_write(UC_ARM64_REG_PC,lr)
 if a==clear+4:
  post_clear.update({n:uc.reg_read(regs[n]) for n in range(19,31)});post_clear['sp']=uc.reg_read(UC_ARM64_REG_SP)
u.hook_add(UC_HOOK_CODE,late);u.emu_start(0xffffffc000f414e4,0xffffffc000f41570,count=3000000)
assert len(observed)==len(clear_args)==1 and {k:v for k,v in post_clear.items() if k!=30}=={k:v for k,v in at_call.items() if k not in ('args',30)} and post_clear[30]==clear+4
assert bytes(u.mem_read(SAVED,0x80000))==stored
assert not any(u.mem_read(CURRENT+832,0x80000-832))
# Console object binary: name16 + write/device/unblank/setup/early_setup => flags at56.
console=0xffffffc001002c28;con=raw[console-base:console-base+96]
# preserve concrete object for independent interpretation rather than guess struct offsets.
(R/'evidence/console-object.hex').write_text(con.hex()+'\n')
(R/'evidence/entry-linked.disasm').write_text(listing(code,APP));(R/'evidence/readback-linked.disasm').write_text(listing(wrapper[:sy['format']-slot],slot))
(R/'evidence/init-before-clear.disasm').write_text(listing(bytes(new[0xec14e4:0xec1574]),0xffffffc000f414e4))
# Gzip, wrappers and padding; exact donor gzip metadata; marker-only DT.
actual_dt=(R/'source/stock-marker-only.dtb').read_bytes();stream=kernel[512:-len(dt)];gz=bytearray(gzip.compress(bytes(new),compresslevel=9,mtime=0));gz[:10]=stream[:10]
new_kernel=b.wrap(kernel,bytes(gz)+actual_dt);image=b.make_image(header,new_kernel,ramdisk);full=image+bytes(b.PARTITION_SIZE-len(image))
# LK scanned-tail and raw-inflate semantic model from pinned offline analysis.
model=lk_contract.model_lk_gzip(new_kernel[512:],len(new_kernel)-512,len(gz),bytes(new))
ah,ak,ar,at=b.parse_image(image);nr,nd=b.ungzip(ak[512:]);assert nr==new and nd==actual_dt and ar==ramdisk and not at
assert ah[:8]==header[:8] and ah[12:576]==header[12:576] and ah[608:]==header[608:]
assert ak[:4]==kernel[:4] and ak[8:512]==kernel[8:512]
assert new[4:64]==raw[4:64] and struct.unpack_from('<Q',new,16)[0]==END-base
assert fdt.parse(nd)[1]['/memory@00000000']['reg']==bytes.fromhex('00000000400000000000000020000000')
cpio,extra=b.ungzip(ar[512:]);assert not extra;helper=b.parse_cpio(cpio)['init'][3];assert b.sha(helper)=='631a0aa5e72ee4110357ddac12bc5e5436ef3b1924cf64355f6fae99dc96d272'
ro=len(ah)+b.align(len(ak));assert not any(image[len(ah)+len(ak):ro]) and not any(image[ro+len(ar):]) and not any(full[len(image):]) and len(full)==16740352
# Installer only exact hashes/length/profile + admitted current complete preimage.
parent=W/'2026-11-07-asus-stock-checkpoint-readback-control';original=(parent/'source/install.py').read_text();current='f547c8fd3819b01efef6a232197aa5670dcbe332a83edcbc20529b2a07a08e42'
line=next(x for x in original.splitlines() if x.startswith('INSTALL_PREIMAGES='));assert current not in line
edits={"IMAGE_SHA='042c1a63a699f6a978c589341801580a5c4f46fde23832ad174f42c763940260'":f"IMAGE_SHA='{b.sha(image)}'","FULL_SHA='d6949069eaa498fcfbc27be707d01dffd7099992c5eb71e2c7c3926639851355'":f"FULL_SHA='{b.sha(full)}'",'len(image)==7745536':f'len(image)=={len(image)}',"profile='stock-3.18.35-a7-current-readback-legacy-ram-usb-control-r1'":"profile='stock-3.18.35-entry-writer-positive-control-r2'",line:line[:-1]+f",'{current}')"}
installer=original
for old,value in edits.items():assert installer.count(old)==1;installer=installer.replace(old,value)
def block(src,name):
 n=next(x for x in ast.parse(src).body if getattr(x,'name',None)==name);return ''.join(src.splitlines(True)[n.lineno-1:n.end_lineno])
for name in ('execute','Transport','Guard'):assert block(original,name)==block(installer,name)
reverse=installer
for old,value in reversed(list(edits.items())):assert reverse.count(value)==1;reverse=reverse.replace(value,old)
assert reverse==original
for name in ('adb','legacy_adb.py','bootformat.py'):(R/'source'/name).write_bytes((parent/'source'/name).read_bytes())
(R/'source/install.py').write_text(installer);(R/'source/install.diff').write_text(''.join(difflib.unified_diff(original.splitlines(True),installer.splitlines(True),fromfile='readback/install.py',tofile='entry-writer-r2/install.py')))
(R/'artifacts/candidate.img').write_bytes(image);(R/'artifacts/candidate.p10.raw').write_bytes(full)
assert (R/'artifacts/candidate.img').read_bytes()==image and (R/'artifacts/candidate.p10.raw').read_bytes()==full
rec=lambda v:dict(bytes=len(v),sha256=b.sha(v))
receipt=dict(status='LOCAL_PACKAGED_NO_PHYSICAL_GO',run_uuid=p['run_uuid'],expected_actual_tag=p['tag'],candidate=rec(image),full_p10=rec(full),donor=rec(blob),raw_before=rec(raw),raw_after=rec(new),ramdisk=rec(ramdisk),helper=rec(helper),dt=rec(nd),entry=dict(virtual=hex(APP),physical=hex(phys(APP)),return_virtual=hex(base+64),return_physical='0x40080040',code_bytes=len(code),tag_address=hex(sy['asus_entry_tag']),append_end=hex(append_end),append_bytes=append_end-APP,inside_original_BSS=True,original_Image_size_unchanged=True),patches=[dict(address=hex(a),raw_offset=hex(a-base),bytes=len(v),before=o.hex(),after=v.hex(),purpose=why) for a,o,v,why in patches],appended_span=dict(raw_offset=hex(len(raw)),bytes=len(new)-len(raw),hex=bytes(new[len(raw):]).hex()),raw_differing_original_bytes=len(changed),lk_model=model,ABI=dict(entry_preserved_x0_x3_x18_x30_SP=True,writer_scratch_only_x4_x17_NZCV=True,unchanged_writer_sha256=b.sha((R/'source/asus_entry_text.S').read_bytes()),actual_pipeline_replays=1,writer_instructions=steps,retained_stores=len(writes),actual_snapshot_text_readback=observed,clear_args=clear_args,clear_unchanged=True,callee_saved_LR_SP_preserved=True,printk_memset_substitutes='Explicit ABI-adversarial local contract stubs; actual kernel printk/reset/registration not emulated'),preservation=dict(only_three_original_raw_spans=True,actual_DT_only_additive_compatible=True,actual_memory_placeholder_unchanged=True,helper_ramdisk_complete=True,header_addresses_bootargs=True,watchdog_reset_unmodified=True,execute_Transport_Guard_adapters_byte_identical=True,installer_only_pins_size_profile_and_current_preimage=True,current_preimage=current),fixture_only_memory_overlay=p['fixture_overlay_only'],limits='Local preparation only. Observed unflattened working stock DT is not pre-MMU x0 or failed 4.9 runtime. Physical stock control still required; missing tag UNKNOWN. Does not prove actual 4.9 DT admission or execution; no experiment 3.',scope=dict(device=False,network=False,SSH=False,cloud=False,private_inputs=False,full_kernel_build=False,VM_start=False,install=False,reboot=False,subagents=False))
(R/'evidence/packaging-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({k:receipt[k] for k in ('status','run_uuid','candidate','full_p10','entry','ABI')},indent=2))
