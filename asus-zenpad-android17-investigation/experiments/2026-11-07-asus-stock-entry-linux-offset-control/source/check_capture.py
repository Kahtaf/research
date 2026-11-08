from pathlib import Path
import sys,struct,json,re,gzip,ast,difflib
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[1];W=R.parent;P=W/'2026-11-07-asus-stock-entry-writer-control-r2'
assert not (R/'evidence/packaging-receipt.json').exists(),'one candidate'
def boundary(event,args):
 if event=='open': assert not any(x in str(args[0]) for x in ('/private/','/device-backup/','root_shell_wifi.py','mtk-su-mirror-b','/dev/'))
 if event.startswith(('socket.','subprocess.')) or event in ('os.system','os.posix_spawn'):raise RuntimeError(event)
sys.addaudithook(boundary)
sys.path.insert(0,str(W/'2026-11-05-asus-android17-device-product/.venv/lib/python3.13/site-packages'))
from elftools.elf.elffile import ELFFile
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_ARM
from unicorn import Uc,UC_ARCH_ARM64,UC_MODE_ARM,UC_HOOK_CODE,UC_HOOK_MEM_WRITE
from unicorn.arm64_const import *
import bootformat as b
sys.path.insert(0,str(W/'2026-11-06-asus-full-boot-lk-contract/scripts'))
import fdt,lk_contract
p=json.loads((P/'evidence/preparation.json').read_text());run=json.loads((R/'evidence/identity.json').read_text())['run_uuid']
base=0xffffffc000080000;APP=0xffffffc0010ad7f0;END=0xffffffc001335000;slot=0xffffffc000696b14;record=0xffffffc000696c40;clear=0xffffffc000f41564;PRINT=0xffffffc000abe7a8;MEMSET=0xffffffc00008a688
phys=lambda a:a-base+0x40080000
blob=(W/'2026-11-07-asus-stock-legacy-ram-usb-reporter/artifacts/candidate.img').read_bytes();header,kernel,ramdisk,trailing=b.parse_image(blob);raw,dt=b.ungzip(kernel[512:]);assert b.sha(blob)=='dc0b98e66798e3abc019f454921b1c84ff3ce58e356e26d0785e05b7714d3427' and b.sha(raw)=='db90ee7fff379f35ac2b0aafb11a6abee7b2c283b57d352c40ae7c6d7c35eb2a'
with (R/'qa/control.elf').open('rb') as fh:
 e=ELFFile(fh);sec={n:(e.get_section_by_name(n)['sh_addr'],e.get_section_by_name(n).data()) for n in ['.entry','.init.rodata','.readback','.record']};sy={s.name:s['st_value'] for s in e.get_section_by_name('.symtab').iter_symbols() if s.name};assert not any(s['sh_type'] in ('SHT_REL','SHT_RELA') for s in e.iter_sections())
assert sy['own_record']==record and sy['own_record_end']==record+40 and record%64==0
assert sec['.readback'][0]==slot and len(sec['.readback'][1])<=300 and sec['.record'][1]==bytes(40)
end=max(a+len(v) for a,v in sec.values() if a>=APP);assert end<0xffffffc001330018 and phys(end)<0x41c80000 and raw[4:64]==raw[4:64]
cs=Cs(CS_ARCH_ARM64,CS_MODE_ARM);code=sec['.entry'][1];ins=list(cs.disasm(code,APP));byaddr={i.address:i for i in ins}
listing=lambda v,a:''.join(f'{i.address:#x} {i.bytes.hex()} {i.mnemonic} {i.op_str}\n' for i in cs.disasm(v,a))
(R/'evidence/entry-linked.disasm').write_text(listing(code,APP));(R/'evidence/readback-linked.disasm').write_text(listing(sec['.readback'][1][:sy['format']-slot],slot))
# Recover source exactly, apart from explicit diagnostic branch destinations and success marker.
orig=(P/'source/asus_entry_text.S').read_text().replace('.Laet_linux:\n\tcmp x14, #0x200','.Laet_linux:\n\tcmp x14, #0x40');changed=(R/'source/asus_entry_text.S').read_text();lines=orig.splitlines(True);sites=json.loads((R/'evidence/source-sites.json').read_text());restored=changed.splitlines(True)
for site in sites: restored[site['line']-1]=lines[site['line']-1]
restored=''.join(restored).replace('\tmov x5, #0xffff\n\tb diag_finish\n.Laet_done:', '.Laet_done:')
assert restored==orig
# Each expanded refusal has a unique ID and source condition; compiled preceding instruction retained.
table=[]
for name,a in sy.items():
 if name.startswith('diag_fail_'):
  n=name.removeprefix('diag_fail_');refs=[i for i in ins if i.mnemonic.startswith(('b.','cb','tb')) and i.op_str.endswith(f'#{a:#x}')];assert len(refs)==1,(name,refs)
  i=refs[0];line=sy['diag_line_'+n];table.append(dict(id=sy['diag_id_'+n],source_line=line,source_condition=lines[line-1].strip(),branch=hex(i.address),actual_branch=i.mnemonic+' '+i.op_str,preceding_test=byaddr[i.address-4].mnemonic+' '+byaddr[i.address-4].op_str,stub=hex(a)))
table.sort(key=lambda x:x['id']);assert len({x['id'] for x in table})==len(table)
(R/'evidence/failure-ids.json').write_text(json.dumps(table,indent=2)+'\n')
(R/'evidence/failure-ids.tsv').write_text('ID\tR2 source line\tcondition\tactual branch\tpreceding test\n'+''.join(f"{x['id']}\t{x['source_line']}\t{x['source_condition']}\t{x['actual_branch']}\t{x['preceding_test']}\n" for x in table)+'65535\tcommit\tunchanged nonzero writer commit completed\tfallthrough\tdsb sy\n')
def branch(a,t,link=False):return struct.pack('<I',(0x94000000 if link else 0x14000000)|(((t-a)//4)&0x3ffffff))
new=bytearray(raw)+bytes(end-base-len(raw));patchedslot=bytearray(raw[slot-base:slot-base+352]);patchedslot[:len(sec['.readback'][1])]=sec['.readback'][1];patchedslot[record-slot:record-slot+40]=bytes(40)
patches=[(base,branch(base,APP),'entry B'),(clear,branch(clear,slot,True),'original-clear BL'),(slot,bytes(patchedslot),'352-byte callback slot including own record')]
assert raw[:4]==bytes.fromhex('10000014') and raw[clear-base:clear-base+4]==bytes.fromhex('4924c597')
for a,v,why in patches:new[a-base:a-base+len(v)]=v
for a,v in sec.values():
 if a>=APP:new[a-base:a-base+len(v)]=v
allowed={i for a,v,_ in patches for i in range(a-base,a-base+len(v))};diff={i for i in range(len(raw)) if raw[i]!=new[i]};assert diff<=allowed
# Bounded original slot/table bytes against the prior already-audited exact donor.
prior=json.loads((P/'evidence/packaging-receipt.json').read_text());oldslot=next(x for x in prior['patches'] if x['raw_offset']=='0x616b14');assert raw[slot-base:slot-base+len(bytes.fromhex(oldslot['before']))].hex()==oldslot['before']
assert struct.unpack_from('<Q',raw,0xffffffc001002ef8-base)[0]==slot
regs=[UC_ARM64_REG_X0+i for i in range(29)]+[UC_ARM64_REG_X29,UC_ARM64_REG_X30]
FDT=0x47000000;RET=0x44400000;MAGIC=0x454559535452454e
fixture=(R/'qa/fixture-runtime-memory.dtb').read_bytes();bad=bytearray(fixture);needle=bytes.fromhex('0000000040000000000000007d600000');assert bad.count(needle)==1;at=bad.index(needle);bad[at:at+16]=bytes.fromhex('00000000400000000000000020000000')
tag=sec['.init.rodata'][1][sy['asus_entry_tag']-sec['.init.rodata'][0]:sy['asus_entry_tag_end']-sec['.init.rodata'][0]]
assert run.encode() in tag and len(tag)==234
results=[];records=[];snapshots=[]
cases=[('low-LK-offset',[0x43474244,64,64,0,64,128,64],65535,0xc0),('no-LK-fallback',[0x43474244,64,64,0,0,0,0],65535,0x200),('LK-header-overlap',[0x43474244,64,64,0,32,96,64],None,None),('LK-platform-overlap',[0x43474244,64,128,64,128,192,64],None,None)]
for name,geometry,expected,expected_offset in cases:
 el=8;sctlr=0x30c50830;tree=fixture
 u=Uc(UC_ARCH_ARM64,UC_MODE_ARM);u.mem_map(0x40080000,(len(new)+4095)&~4095);u.mem_write(0x40080000,bytes(new));u.mem_map(FDT,(len(tree)+4095)&~4095);u.mem_write(FDT,tree);u.mem_map(RET,0x80000)
 incoming=bytearray(b'P'*0x80000);struct.pack_into('<7I',incoming,0,*geometry);u.mem_write(RET,bytes(incoming))
 for n,r in enumerate(regs):u.reg_write(r,FDT if n==0 else 0x123400000000+n)
 u.reg_write(UC_ARM64_REG_SP,0x76543000);writes=[];mrs_seen=[];cleans=[]
 def early(uc,a,size,data):
  i=byaddr.get(a-0x40080000+base)
  if i and i.mnemonic=='mrs':
   dst,reg=i.op_str.split(', ');reg=reg.lower();val=el if reg=='currentel' else sctlr
   assert reg=='currentel' or reg==('sctlr_el1' if el==4 else 'sctlr_el2');mrs_seen.append(reg);uc.reg_write(regs[int(dst[1:])],val);uc.reg_write(UC_ARM64_REG_PC,a+4)
  if i and i.mnemonic=='dc':
   op,r=i.op_str.split(', ');assert op=='cvac';cleans.append(uc.reg_read(regs[int(r[1:])]))
   uc.reg_write(UC_ARM64_REG_PC,a+4)
 def store(uc,access,a,size,v,data):writes.append((a,size,v))
 u.hook_add(UC_HOOK_CODE,early);u.hook_add(UC_HOOK_MEM_WRITE,store);u.emu_start(0x40080000,0x40080040,count=2000000);assert u.reg_read(UC_ARM64_REG_PC)==0x40080040
 for n in (0,1,2,3,*range(18,31)):assert u.reg_read(regs[n])==(FDT if n==0 else 0x123400000000+n)
 assert u.reg_read(UC_ARM64_REG_SP)==0x76543000
 rec=bytes(u.mem_read(phys(record),40));fields=struct.unpack('<5Q',rec);assert fields[:4]==(MAGIC,FDT,el,sctlr)
 assert cleans==[phys(record),phys(record)+16,phys(record)+32]
 assert all((phys(record)<=a and a+size<=phys(record)+40) or (RET<=a and a+size<=RET+0x80000) for a,size,v in writes)
 retained=[x for x in writes if RET<=x[0]<RET+0x80000]
 if expected==65535:
  assert fields[4]==65535 and bytes(u.mem_read(RET+struct.unpack('<I',bytes(u.mem_read(RET+0x30,4)))[0],len(tag)))==tag and retained
  assert struct.unpack('<I',bytes(u.mem_read(RET+0x2c,4)))[0]==expected_offset
 else:
  assert not retained and fields[4] in [x['id'] for x in table]
  assert next(x for x in table if x['id']==fields[4])['source_line']==(682 if name=='LK-header-overlap' else 684)
 reason=next((x for x in table if x['id']==fields[4]),dict(source_condition='success commit'))
 results.append(dict(case=name,fields=list(map(hex,fields)),failure=reason,mrs=mrs_seen,clean_addresses=list(map(hex,cleans)),retained_stores=len(retained),ABI_preserved=True));records.append(rec);snapshots.append(bytes(u.mem_read(RET,0x80000)))
# Late actual wrapper, original callsite BL, adversarial printk/clear ABI. Zero record printed too.
late_results=[]
for case_index,rec in enumerate(records+[bytes(40)]):
 u=Uc(UC_ARCH_ARM64,UC_MODE_ARM);u.mem_map(base,(END-base+4095)&~4095);u.mem_write(base,bytes(new));u.mem_write(record,rec);STACK=0x62000000;CURRENT=0x60000000;u.mem_map(STACK,0x10000);u.mem_map(CURRENT,0x80000);snapshot=snapshots[case_index] if case_index<len(snapshots) else bytes(0x80000);u.mem_write(CURRENT,snapshot);u.mem_write(sy['saved'],struct.pack('<Q',CURRENT if case_index<len(snapshots) else 0))
 for n,r in enumerate(regs):u.reg_write(r,0x123400000000+n)
 u.reg_write(UC_ARM64_REG_SP,STACK+0x8000);u.reg_write(regs[0],CURRENT);u.reg_write(regs[1],0);u.reg_write(regs[2],0x80000)
 before={n:u.reg_read(regs[n]) for n in range(19,30)};before[18]=u.reg_read(regs[18]);sp=u.reg_read(UC_ARM64_REG_SP);prints=[];cleared=[]
 def late(uc,a,size,data):
  if a==PRINT:
   ptr=uc.reg_read(regs[0]);fmt=bytes(uc.mem_read(ptr,200)).split(b'\0')[0].decode()
   if not prints:
    args=[uc.reg_read(regs[n]) for n in range(1,6)];assert args==list(struct.unpack('<5Q',rec));assert run in fmt
    prints.append(dict(format=fmt,actual_fields=list(map(hex,args))))
   else:
    assert fmt=='\x011%.*s' and not cleared
    length=uc.reg_read(regs[1]);text_ptr=uc.reg_read(regs[2]);assert length==len(tag)
    assert text_ptr==CURRENT+struct.unpack_from('<I',snapshot,0x30)[0]
    actual=bytes(uc.mem_read(text_ptr,length));assert actual==tag and run.encode() in actual
    prints.append(dict(format=fmt,actual_pointer=hex(text_ptr),actual_bytes=actual.hex(),actual_text=actual.decode(),complete_fresh_OEM_tag=True))
  elif a==MEMSET:
   args=[uc.reg_read(regs[n]) for n in range(3)];assert args==[CURRENT,0,0x80000];uc.mem_write(CURRENT,bytes(0x80000));cleared.append(args)
  else:return
  lr=uc.reg_read(regs[30])
  for n in range(18):uc.reg_write(regs[n],0xc0de0000+n)
  uc.reg_write(UC_ARM64_REG_PC,lr)
 u.hook_add(UC_HOOK_CODE,late);u.emu_start(clear,clear+4,count=10000);assert len(cleared)==1 and len(prints)==(2 if case_index<2 else 1)
 assert all(u.reg_read(regs[n])==v for n,v in before.items()) and u.reg_read(regs[30])==clear+4 and u.reg_read(UC_ARM64_REG_SP)==sp
 assert bytes(u.mem_read(CURRENT,0x80000))==bytes(0x80000);late_results.append(dict(case=cases[case_index][0] if case_index<4 else 'zero-early-record',prints=prints,clear=cleared[0],ABI_preserved=True,record_commit=struct.unpack('<5Q',rec)[4]==65535,actual_complete_fresh_OEM_tag=len(prints)==2))
(R/'evidence/replay.json').write_text(json.dumps(dict(early=results,late=late_results,limitations='MRS system state supplied explicitly; DC CVAC decoded and its operand addresses checked, cache effects not emulated. printk and memset are ABI-adversarial contract substitutes. No physical execution or retention claim.'),indent=2)+'\n')
actual_dt=(R/'source/stock-marker-only.dtb').read_bytes();stream=kernel[512:-len(dt)];gz=bytearray(gzip.compress(bytes(new),compresslevel=9,mtime=0));gz[:10]=stream[:10];nk=b.wrap(kernel,bytes(gz)+actual_dt);image=b.make_image(header,nk,ramdisk);full=image+bytes(b.PARTITION_SIZE-len(image));model=lk_contract.model_lk_gzip(nk[512:],len(nk)-512,len(gz),bytes(new))
ah,ak,ar,at=b.parse_image(image);nr,nd=b.ungzip(ak[512:]);assert nr==new and nd==actual_dt and ar==ramdisk and not at and len(full)==16740352 and not any(full[len(image):]);assert new[4:64]==raw[4:64]
assert ah[12:576]==header[12:576] and ah[608:]==header[608:] and ak[8:512]==kernel[8:512]
cpio,extra=b.ungzip(ar[512:]);helper=b.parse_cpio(cpio)['init'][3];assert not extra and b.sha(helper)=='631a0aa5e72ee4110357ddac12bc5e5436ef3b1924cf64355f6fae99dc96d272'
assert fdt.parse(nd)[1]['/memory@00000000']['reg']==bytes.fromhex('00000000400000000000000020000000')
B=W/'2026-11-07-asus-stock-entry-refusal-capture'
original=(B/'source/install.py').read_text();current='10c4c72da182f8164c238c27901b855e963eb1b5b66bb13827878f9f9c64370e';line=next(x for x in original.splitlines() if x.startswith('INSTALL_PREIMAGES='));assert current not in line
edits={"IMAGE_SHA='5ec1fb9af889dfaaa383af416c1ed429c0d4f3d46d6cb1b2107057a9e79f92f6'":f"IMAGE_SHA='{b.sha(image)}'","FULL_SHA='10c4c72da182f8164c238c27901b855e963eb1b5b66bb13827878f9f9c64370e'":f"FULL_SHA='{b.sha(full)}'",'len(image)==7747584':f'len(image)=={len(image)}',"profile='stock-3.18.35-entry-refusal-capture'":"profile='stock-3.18.35-entry-linux-offset-control'",line:line[:-1]+f",'{current}')"}
installer=original
for a,v in edits.items():assert installer.count(a)==1;installer=installer.replace(a,v)
def block(src,name):
 node=next(x for x in ast.parse(src).body if getattr(x,'name',None)==name);return ''.join(src.splitlines(True)[node.lineno-1:node.end_lineno])
for name in ['execute','Transport','Guard']:assert block(original,name)==block(installer,name)
rev=installer
for a,v in reversed(list(edits.items())):rev=rev.replace(v,a)
assert rev==original
(R/'source/install.py').write_text(installer);(R/'source/install.diff').write_text(''.join(difflib.unified_diff(original.splitlines(True),installer.splitlines(True),fromfile='capture/install.py',tofile='linux-offset-control/install.py')))
(R/'artifacts/candidate.img').write_bytes(image);(R/'artifacts/candidate.p10.raw').write_bytes(full)
receipt=dict(status='LOCAL_CANDIDATE_FOCUSED_REPLAY_PASSED',run_uuid=run,candidate=dict(bytes=len(image),sha256=b.sha(image)),full_p10=dict(bytes=len(full),sha256=b.sha(full)),raw_before=dict(bytes=len(raw),sha256=b.sha(raw)),raw_after=dict(bytes=len(new),sha256=b.sha(new)),entry=dict(virtual=hex(APP),physical=hex(phys(APP)),return_virtual=hex(base+64),return_physical=hex(phys(base+64)),bytes=len(code),append_end=hex(end)),record=dict(virtual=hex(record),physical=hex(phys(record)),bytes=40,fields=['magic','original_x0','CurrentEL','valid_SCTLR_or_ffffffffffffffff','status'],magic=hex(MAGIC),initial='all zero',outside_BSS=True),slot=dict(address=hex(slot),end=hex(slot+352),wrapper_code=sy['format']-slot,wrapper_and_format=len(sec['.readback'][1]),record_offset=record-slot,remaining=slot+352-(record+40)),patches=[dict(address=hex(a),raw_offset=hex(a-base),bytes=len(v),before=raw[a-base:a-base+len(v)].hex(),after=v.hex(),purpose=why) for a,v,why in patches],append_hex=bytes(new[len(raw):]).hex(),differing_original_bytes=len(diff),failure_branch_count=len(table),lk_model=model,helper_sha256=b.sha(helper),ramdisk_sha256=b.sha(ramdisk),dt_sha256=b.sha(nd),current_preimage=current,installer_execute_Transport_Guard_adapters_unchanged=True,only_parent_linux_lower_bound_changed=True,retained_stores_unchanged=True,scope=dict(device=False,network=False,SSH=False,cloud=False,private_inputs=False,full_kernel_build=False,VM_start=False,install=False,reboot=False,subagents=False))
(R/'evidence/packaging-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({k:receipt[k] for k in ['status','run_uuid','candidate','full_p10','slot']},indent=2))
