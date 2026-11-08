from pathlib import Path
import json,hashlib,subprocess,re,struct,zlib
from source_checks import check,PM
R=Path('/srv/android/asus-linux49-pmic-stage-capture-20261108-a1ff82b1');B=Path('/srv/android/asus-linux49-power-supply-phase-capture-20261107-431dfb9c');K=R/'kernel';O=R/'out';E=R/'evidence'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();i=json.loads((R/'source/identity.json').read_text())
assert json.loads((E/'build-status.json').read_text())['status']=='complete'
for n,v in json.loads((E/'source-pins.json').read_text()).items():assert sha(K/n)==v['after'] and sha(B/'kernel'/n)==v['before']
assert (O/'.config').read_bytes()==(B/'out/.config').read_bytes() and sha(O/'.config')==i['config_sha256']
assert (O/'source').resolve()==K
preserved=json.loads((E/'preserved-source-pins.json').read_text())
for n,v in preserved.items():assert sha(K/n)==sha(B/'kernel'/n)==v,n
for n in ['arch/arm64/kernel/head.S','arch/arm64/kernel/asus_entry_text.S','arch/arm64/boot/dts/asus/asus-p00a.dts','drivers/power/supply/power_supply_leds.c','drivers/power/supply/power_supply_sysfs.c']:
 assert (K/n).exists()==(B/'kernel'/n).exists()
 if (K/n).exists():assert (K/n).read_bytes()==(B/'kernel'/n).read_bytes();preserved[n]=sha(K/n)
scoped=check(K,B/'kernel',i['run_uuid']);(E/'source-checks.json').write_text(json.dumps(scoped,indent=2)+'\n')
freeze=json.loads((E/'base-freeze.json').read_text());inodes={}
for n,v in freeze.items():
 p=B/n;r=R/n;assert sha(p)==v['sha256'] and p.stat().st_ino==v['inode'] and p.stat().st_mtime_ns==v['mtime_ns'],n
 assert p.stat().st_ino!=r.stat().st_ino,n
 inodes[n]=dict(base_unchanged=True,base_inode=p.stat().st_ino,candidate_inode=r.stat().st_ino,independent=True)
(E/'repository-preservation.json').write_text(json.dumps(dict(status='PASS_SCOPED_FROZEN_BASE_AND_INDEPENDENT_INODES',whole_directory_cp_a_reflink_auto=True,scope=inodes,no_git_commands=True,nested_repository_tree_preserved_by_copy=True,no_full_tree_audit=True),indent=2)+'\n')
nm=subprocess.check_output(['aarch64-linux-gnu-nm','-S','--defined-only',str(O/'vmlinux')],text=True)
sized={p[3]:(int(p[0],16),int(p[1],16)) for l in nm.splitlines() if len(p:=l.split())==4};sym={}
for l in subprocess.check_output(['aarch64-linux-gnu-nm','-an',str(O/'vmlinux')],text=True).splitlines():
 p=l.split()
 if len(p)==3:sym[p[2]]=int(p[0],16)
def dump(a,z):return subprocess.check_output(['aarch64-linux-gnu-objdump','-d','--start-address='+hex(a),'--stop-address='+hex(a+z),str(O/'vmlinux')],text=True)
init=dump(*sized['asus_retained_trace_init']);a=int(re.search(r'\bbl\s+([0-9a-f]+) <trace_init>',init).group(1),16)
sized['trace_init']=next((int(p[0],16),int(p[1],16)) for l in nm.splitlines() if len(p:=l.split())==4 and p[3]=='trace_init' and int(p[0],16)==a)
driver=['asus_p00a_pmic_present','asus_p00a_pmic_adc','p00a_pmic_prepare_adc','asus_p00a_battery_get_property','battery_get_property','asus_p00a_pmic_enable_baton','pmic_read_interface','pmic_read_interface_nolock','pmic_config_interface','pmic_config_interface_nolock']
oldnames=['power_supply_changed_work','power_supply_get_property','process_one_work','finish_task_switch','asus_capture_switch','ktime_get_ts64','arch_counter_read','__clean_dcache_area_poc','_raw_spin_trylock','_raw_spin_unlock_irqrestore','trace_init','cap_init']
pm_names={'pm_fault','pm_header','pm_init','pm_ps_field','pm_property','pm_record','asus_capture_pmic_begin','asus_capture_pmic_step'}
objnm=subprocess.check_output(['aarch64-linux-gnu-nm','-S','--defined-only',str(O/'arch/arm64/kernel/asus_retained_trace.o')],text=True)
object_sizes={x[3]:int(x[1],16) for l in objnm.splitlines() if len(x:=l.split())==4}
actual_pm_names={n.split('.')[0] for n in object_sizes} & pm_names
# Local symbols can collide across translation units. Resolve by actual object
# name AND size, then confirm initializer is called by the recorder trace_init.
for n,z in object_sizes.items():
 if n.split('.')[0] in actual_pm_names:
  matches=[(int(x[0],16),int(x[1],16)) for l in nm.splitlines() if len(x:=l.split())==4 and x[3]==n and int(x[1],16)==z]
  assert len(matches)==1,(n,matches)
  sized[n]=matches[0]
names=[n for n in sized if n.split('.')[0] in set(driver+oldnames)|actual_pm_names or n.startswith('arch_timer_handler_') or n.split('.')[0]=='sw_commit']
dis={n:dump(*sized[n]) for n in names if sized[n][1]}
(E/'scoped-hooks.disasm').write_text('\n'.join(dis.values()))
rec={n:v for n,v in dis.items() if n.split('.')[0] in actual_pm_names}
calls={n:sorted(set(re.findall(r'\b(?:bl|b)\s+[0-9a-f]+ <([^>]+)>',v))) for n,v in rec.items()}
allowed={'__clean_dcache_area_poc','memcpy','memcmp','memset','__memset','__memcpy','__memcmp','cap_hex','__stack_chk_fail','_raw_spin_trylock','_raw_spin_unlock_irqrestore','sw_commit'}
for n,targets in calls.items():
 for t in targets:assert t.split('+')[0].split('.')[0] in allowed|pm_names,(n,t)
record=next(v for n,v in rec.items() if n.split('.')[0]=='pm_record')
assert len(re.findall(r'\bmrs\s+x\d+, cntvct_el0',record))==1 and not any(re.search(r'\bblr\b',v) for v in rec.values())
assert '<_raw_spin_unlock_irqrestore>' in record and '<_raw_spin_trylock>' in record
assert re.search(r'\bdsb\s+sy',dis['__clean_dcache_area_poc'])
# Relevant original primitives appear once per source call site, except compiler
# duplicate error unlock paths. Hook arguments and actual branches are retained.
body=lambda prefix:'\n'.join(v for n,v in dis.items() if n.split('.')[0]==prefix)
adc=body('asus_p00a_pmic_adc');present=body('asus_p00a_pmic_present');prep=body('p00a_pmic_prepare_adc');battery=body('asus_p00a_battery_get_property')
assert present.count('<pmic_read_interface>')==1
for target,count in [('__pm_stay_awake',1),('mutex_lock',1),('pmic_config_interface',3),('__const_udelay',1),('pmic_read_interface',1),('mutex_unlock',1),('__pm_relax',1)]:assert adc.count('<'+target+'>')==count,(target,adc.count('<'+target+'>'))
assert '<asus_capture_pmic_begin>' in present and '<asus_capture_pmic_step>' in present and '<asus_capture_pmic_begin>' in adc and '<asus_capture_pmic_step>' in adc
combined=adc+prep
for target in ['_raw_spin_lock_irqsave','_raw_spin_unlock_irqrestore','usleep_range','pmic_config_interface_nolock']:assert '<'+target+'>' in combined,target
# Return addresses are actual BL+4 sites, bound to exact caller function body.
def returns(disasm,target):return [int(m.group(1),16)+4 for m in re.finditer(r'^\s*([0-9a-f]+):.*\bbl\s+[0-9a-f]+ <'+re.escape(target)+r'>',disasm,re.M)]
present_returns=returns(battery,'asus_p00a_pmic_present');adc_returns=returns(battery,'asus_p00a_pmic_adc');assert present_returns and len(adc_returns)==2
voltage=[]
for ret in adc_returns:
 lines=battery.splitlines();at=next(j for j,l in enumerate(lines) if l.lstrip().startswith(hex(ret-4)[2:]+':'));prior='\n'.join(lines[max(0,at-5):at]);
 if re.search(r'\bmov\s+w0, #0x6\b',prior) and re.search(r'\bmov\s+w1, #0x5\b',prior):voltage.append(ret)
assert len(voltage)==1,voltage
prepare_returns=returns(adc,'p00a_pmic_prepare_adc')
if not prepare_returns:
 # A single-caller static prepare can be inlined. Its return-address builtin
 # then has the enclosing exported ADC's caller, rather than a fictional frame.
 assert not prep and combined.count('<asus_capture_pmic_begin>')==2
 prepare_returns=adc_returns
else:assert prep and len(prepare_returns)==1
assert '<asus_p00a_battery_get_property>' in body('battery_get_property')
assert '<asus_capture_switch>' in body('finish_task_switch') and '<asus_capture_mono_enter>' in body('ktime_get_ts64') and '<asus_capture_counter_enter>' in body('arch_counter_read')
assert '<asus_capture_work_enter>' in body('process_one_work') and '<asus_capture_work_return>' in body('process_one_work')
handlers={n:v for n,v in dis.items() if n.startswith('arch_timer_handler_')};assert handlers and all('<asus_capture_event_enter>' in v and '<asus_capture_exit>' in v for v in handlers.values())
assert '<pm_init>' in body('trace_init')
assert '#0x687f' in body('trace_init'),'actual combined OEM console capacity 26752 check'
raw=(O/'arch/arm64/boot/Image').read_bytes();text=sym['_text'];a,z=sym['asus_entry_tag'],sym['asus_entry_tag_end'];assert raw[a-text:z-text]==i['tag'].encode()
for tag in ['A49CAP1','A49SW2','A49WD1','A49PS1','A49PM1']:assert (tag+' uuid='+i['run_uuid']).encode() in raw
assert b'ASUS49-DIAG headless RDMA IRQ registration skipped' in raw
image_size=struct.unpack_from('<Q',raw,16)[0];assert image_size==sym['_end']-text and image_size>=len(raw)
def ungzip(p):
 d=zlib.decompressobj(31);r=d.decompress(p);assert d.eof;return r,d.unused_data
_,dt=ungzip((O/'arch/arm64/boot/Image.gz-dtb').read_bytes());_,bdt=ungzip((B/'out/arch/arm64/boot/Image.gz-dtb').read_bytes());assert dt==bdt
assert sha(B/'out/arch/arm64/boot/Image.gz-dtb')==i['base_compiled_sha256']
result=dict(status='PASS_SCOPED_SOURCE_AND_ACTUAL_ELF',entry_identity=i,Image=dict(file_bytes=len(raw),image_size=image_size,text=hex(text),end=hex(sym['_end'])),preserved_sources=preserved,recorder_calls=calls,raw_CNTVCT_reads=1,indirect_recorder_calls=0,cache_clean_barrier='actual linked dsb sy',source_checks=scoped,config_byte_identical=True,hardware_DTB_byte_identical=True,hardware_DTB_sha256=hashlib.sha256(dt).hexdigest(),compiler_stack_protector='inherited canary-failure-only __stack_chk_fail',old_capture_area_bytes=20544,pmic_capture_area_bytes=6208,combined_bytes=26752,pmic_callers=dict(present_returns=present_returns,voltage_adc_returns=voltage,prepare_returns=prepare_returns,prepare_inlined=not bool(prep)),symbols={n:dict(address=hex(sized[n][0]),bytes=sized[n][1]) for n in names if n in sized},physical_execution=False)
(E/'linked-capture.json').write_text(json.dumps(result,indent=2)+'\n')
(E/'linked-seams.json').write_text(json.dumps({n:['\n'.join(v.splitlines()[max(0,j-7):j+5]) for j,l in enumerate(v.splitlines()) if re.search(r'\bbl\s',l)] for n,v in dis.items() if n.split('.')[0] in set(driver)|pm_names},indent=2)+'\n')
print(json.dumps(dict(status=result['status'],pmic_callers=result['pmic_callers'],combined_bytes=26752),indent=2))
