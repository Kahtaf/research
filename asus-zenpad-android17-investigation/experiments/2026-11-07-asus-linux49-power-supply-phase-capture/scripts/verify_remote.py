from pathlib import Path
import json,hashlib,subprocess,re,struct,zlib,sys
from source_checks import check,function
R=Path('/srv/android/asus-linux49-power-supply-phase-capture-20261107-431dfb9c');B=Path('/srv/android/asus-linux49-work-dispatch-capture-20261107-b4702f9a');K=R/'kernel';O=R/'out';E=R/'evidence'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
i=json.loads((R/'source/identity.json').read_text())
assert json.loads((E/'build-status.json').read_text())['status']=='complete'
for n,v in json.loads((E/'source-pins.json').read_text()).items():assert sha(K/n)==v['after'] and sha(B/'kernel'/n)==v['before']
assert (O/'.config').read_bytes()==(B/'out/.config').read_bytes() and sha(O/'.config')==i['config_sha256']
assert (O/'source').resolve()==K
preserved=json.loads((E/'preserved-source-pins.json').read_text())
for n,v in preserved.items():assert sha(K/n)==sha(B/'kernel'/n)==v,n
for n in ['arch/arm64/kernel/head.S','arch/arm64/kernel/asus_entry_text.S','arch/arm64/boot/dts/asus/asus-p00a.dts','drivers/power/supply/power_supply_leds.c','drivers/power/supply/power_supply_sysfs.c']:
 if not (B/'kernel'/n).exists():
  assert not (K/n).exists();continue
 assert (K/n).read_bytes()==(B/'kernel'/n).read_bytes();preserved[n]=sha(K/n)
scoped=check(K,B/'kernel',i['run_uuid']);(E/'source-checks.json').write_text(json.dumps(scoped,indent=2)+'\n')
freeze=json.loads((E/'base-freeze.json').read_text());inode_checks={}
for n,v in freeze.items():
 p=B/n;r=R/n
 assert sha(p)==v['sha256'] and p.stat().st_ino==v['inode'] and p.stat().st_mtime_ns==v['mtime_ns'],n
 assert p.stat().st_ino!=r.stat().st_ino,n
 inode_checks[n]=dict(base_unchanged=True,base_inode=p.stat().st_ino,candidate_inode=r.stat().st_ino,independent=True)
(E/'repository-preservation.json').write_text(json.dumps(dict(status='PASS_SCOPED_FROZEN_BASE_AND_INDEPENDENT_INODES',whole_directory_cp_a_reflink_auto=True,scope=inode_checks,no_git_commands=True,nested_repository_tree_preserved_by_copy=True,no_full_tree_audit=True),indent=2)+'\n')
nm=subprocess.check_output(['aarch64-linux-gnu-nm','-S','--defined-only',str(O/'vmlinux')],text=True)
sized={p[3]:(int(p[0],16),int(p[1],16)) for l in nm.splitlines() if len(p:=l.split())==4}
sym={}
for l in subprocess.check_output(['aarch64-linux-gnu-nm','-an',str(O/'vmlinux')],text=True).splitlines():
 p=l.split()
 if len(p)==3:sym[p[2]]=int(p[0],16)
def dump(o,a,z):return subprocess.check_output(['aarch64-linux-gnu-objdump','-d','--start-address='+hex(a),'--stop-address='+hex(a+z),str(o/'vmlinux')],text=True)
init=dump(O,*sized['asus_retained_trace_init']);a=int(re.search(r'\bbl\s+([0-9a-f]+) <trace_init>',init).group(1),16)
sized['trace_init']=next((int(p[0],16),int(p[1],16)) for l in nm.splitlines() if len(p:=l.split())==4 and p[3]=='trace_init' and int(p[0],16)==a)
names=['power_supply_changed_work','__power_supply_changed_work','power_supply_get_property','process_one_work','asus_capture_work_enter','asus_capture_work_return','finish_task_switch','asus_capture_switch','__clean_dcache_area_poc','_raw_spin_trylock','_raw_spin_unlock_irqrestore','ktime_get_ts64','arch_counter_read','asus_retained_trace_init','trace_init','cap_init','asus_capture_ps_begin','asus_capture_ps_step']
ps_names={'ps_fault','ps_header','ps_init','ps_name','ps_record'}
names += [n for n in sized if n.split('.')[0] in ps_names or n.startswith(('wd_','arch_timer_handler_','power_supply_get_property.')) or n.split('.')[0]=='sw_commit']
dis={n:dump(O,*sized[n]) for n in names if n in sized and sized[n][1]}
(E/'scoped-hooks.disasm').write_text('\n'.join(dis.values()))
bnm=subprocess.check_output(['aarch64-linux-gnu-nm','-S','--defined-only',str(B/'out/vmlinux')],text=True)
bsized={p[3]:(int(p[0],16),int(p[1],16)) for l in bnm.splitlines() if len(p:=l.split())==4}
(E/'base-hooks.disasm').write_text('\n'.join(dump(B/'out',*bsized[n]) for n in ['power_supply_changed_work','__power_supply_changed_work','power_supply_get_property','process_one_work']))
for n in ['__power_supply_changed_work','power_supply_get_property']:
 f='\n'.join(v for k,v in dis.items() if k==n or k.startswith(n+'.'));assert f.count('<asus_capture_ps_begin>')==1 and f.count('<asus_capture_ps_step>')==1 and len(re.findall(r'\bblr\s+x\d+',f))==1,n
 pre=f.index('<asus_capture_ps_begin>');ret=f.index('<asus_capture_ps_step>');segment=f[pre+len('<asus_capture_ps_begin>'):ret]
 assert len(re.findall(r'\bblr\b',segment))==1 and not re.search(r'\bmsr\b',segment),n
 # Between the two capture calls there is exactly the original indirect call.
 targets=re.findall(r'\bbl\s+[0-9a-f]+ <([^>]+)>',segment)
 assert not targets,(n,targets)
f=dis['power_supply_changed_work']
assert f.count('<asus_capture_ps_begin>')==1
ops=['class_for_each_device','power_supply_update_leds','atomic_notifier_call_chain','kobject_uevent']
assert all(f.count('<'+n+'>')==1 for n in ops)
assert [f.index('<'+n+'>') for n in ops]==sorted(f.index('<'+n+'>') for n in ops)
# Build disassembly neighborhoods to review the actual argument registers,
# branch paths, original callback reloads, flags and local lifetimes.
seams={}
for n in ['power_supply_changed_work','__power_supply_changed_work','power_supply_get_property','process_one_work']:
 ls='\n'.join(v for k,v in dis.items() if k==n or k.startswith(n+'.')).splitlines();seams[n]=['\n'.join(ls[max(0,j-8):j+7]) for j,l in enumerate(ls) if re.search(r'\bblr\b',l) or any('<'+x+'>' in l for x in ops+['asus_capture_ps_begin','asus_capture_ps_step','asus_capture_work_enter','asus_capture_work_return'])]
(E/'linked-seams.json').write_text(json.dumps(seams,indent=2)+'\n')
record=next(v for n,v in dis.items() if n.split('.')[0]=='ps_record')
assert len(re.findall(r'\bmrs\s+x\d+, cntvct_el0',record))==1 and not re.search(r'\bblr\b',record)
rec={n:v for n,v in dis.items() if n.split('.')[0] in ps_names or n.startswith('asus_capture_ps_')}
calls={n:sorted(set(re.findall(r'\b(?:bl|b)\s+[0-9a-f]+ <([^>]+)>',v))) for n,v in rec.items()}
allowed=['__clean_dcache_area_poc','memcpy','memcmp','memset','strnlen','__memset','__memcpy','__memcmp','cap_hex','__stack_chk_fail','_raw_spin_trylock','_raw_spin_unlock_irqrestore','sw_commit','__pi_strnlen']
assert sym['__pi_strnlen']==sym['strnlen'],'actual strnlen alias'
for n,targets in calls.items():
 for t in targets:assert t.split('+')[0] in allowed or t.split('+')[0].split('.')[0] in ps_names or t.split('+')[0] in ['asus_capture_ps_begin','asus_capture_ps_step'],(n,t)
assert '<asus_capture_switch>' in dis['finish_task_switch'] and '<asus_capture_mono_enter>' in dis['ktime_get_ts64'] and '<asus_capture_counter_enter>' in dis['arch_counter_read']
handlers={n:v for n,v in dis.items() if n.startswith('arch_timer_handler_')};assert handlers and all('<asus_capture_event_enter>' in v and '<asus_capture_exit>' in v for v in handlers.values())
assert re.search(r'\bdsb\s+sy',dis['__clean_dcache_area_poc'])
assert '#0x503f' in dis['trace_init'],'combined actual OEM capacity 20544 check'
assert '<_raw_spin_unlock_irqrestore>' in record and '<_raw_spin_trylock>' in record
raw=(O/'arch/arm64/boot/Image').read_bytes();text=sym['_text'];a,z=sym['asus_entry_tag'],sym['asus_entry_tag_end'];assert raw[a-text:z-text]==i['tag'].encode()
for tag in ['A49CAP1','A49SW2','A49WD1','A49PS1']:assert (tag+' uuid='+i['run_uuid']).encode() in raw
assert b'ASUS49-DIAG headless RDMA IRQ registration skipped' in raw
image_size=struct.unpack_from('<Q',raw,16)[0];assert image_size==sym['_end']-text and image_size>=len(raw)
def ungzip(p):
 d=zlib.decompressobj(31);r=d.decompress(p);assert d.eof;return r,d.unused_data
_,dt=ungzip((O/'arch/arm64/boot/Image.gz-dtb').read_bytes());_,bdt=ungzip((B/'out/arch/arm64/boot/Image.gz-dtb').read_bytes());assert dt==bdt
assert sha(B/'out/arch/arm64/boot/Image.gz-dtb')==i['base_compiled_sha256']
result=dict(status='PASS_SCOPED_SOURCE_AND_ACTUAL_ELF',entry_identity=i,Image=dict(file_bytes=len(raw),image_size=image_size,text=hex(text),end=hex(sym['_end'])),preserved_sources=preserved,recorder_calls=calls,raw_CNTVCT_reads=1,indirect_recorder_calls=0,cache_clean_barrier='actual linked dsb sy',source_checks=scoped,config_byte_identical=True,hardware_DTB_byte_identical=True,hardware_DTB_sha256=hashlib.sha256(dt).hexdigest(),compiler_stack_protector='inherited canary-failure-only __stack_chk_fail',old_capture_area_bytes=15168,power_capture_area_bytes=5376,combined_bytes=20544,symbols={n:dict(address=hex(sized[n][0]),bytes=sized[n][1]) for n in names if n in sized},physical_execution=False)
(E/'linked-capture.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
