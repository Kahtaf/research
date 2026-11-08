from pathlib import Path
import json,hashlib,subprocess,re,struct,zlib,gzip
R=Path('/srv/android/asus-linux49-work-dispatch-capture-20261107-b4702f9a');B=Path('/srv/android/asus-linux49-active-work-capture-20261107-8e5c5d4d');K=R/'kernel';O=R/'out';E=R/'evidence'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert json.loads((E/'build-status.json').read_text())['status']=='complete'
pins=json.loads((E/'source-pins.json').read_text())
for n,v in pins.items():assert sha(K/n)==v['after'] and sha(B/'kernel'/n)==v['before']
assert (O/'.config').read_bytes()==(B/'out/.config').read_bytes()
assert sha(O/'.config')=='708a88175ea777c09410000dfe5cf562ccbf764955eb9deaadda7326d0a966e1'
assert (O/'source').resolve()==K
preserved=json.loads((E/'preserved-source-pins.json').read_text())
for n,v in preserved.items():assert sha(K/n)==sha(B/'kernel'/n)==v
for n in ['arch/arm64/kernel/head.S','arch/arm64/kernel/asus_entry_text.S','arch/arm64/boot/dts/asus/asus-p00a.dts']:
 if (K/n).exists():assert (K/n).read_bytes()==(B/'kernel'/n).read_bytes();preserved[n]=sha(K/n)
old=(B/'kernel/arch/arm64/kernel/asus_retained_trace.c').read_text();new=(K/'arch/arm64/kernel/asus_retained_trace.c').read_text()
def function(s,n):
 a=s.index(n+'(');a=s.index('{',a);depth=1;i=a+1
 while depth:depth+=(s[i]=='{')-(s[i]=='}');i+=1
 return s[a:i]
for n in ['cap_hex','cap_fault','cap_publish','cap_lock','cap_enter','cap_match','asus_capture_mono_enter','asus_capture_mono_seq','asus_capture_exit','asus_capture_counter_enter','asus_capture_event_enter','trace_overlaps','trace_check_dt','asus_retained_trace_write','trace_init','sw_commit','sw_fault','sw_header','asus_capture_switch']:
 assert function(old,n)==function(new,n),n
assert function(old,'sw_init').replace('8e5c5d4d-6f94-4569-bfc6-63d92bac94a4','b4702f9a-6b32-423f-b789-d2bd515c0707')==function(new,'sw_init')
ci=function(new,'cap_init');restored=ci.replace(' BUILD_BUG_ON(WD_SIZE % 64);\n','').replace('CAP_SIZE + SW_SIZE + WD_SIZE','CAP_SIZE + SW_SIZE').replace(' wd_init(dest + CAP_SIZE + SW_SIZE);\n','').replace(' smp_store_release(&wd_area, dest + CAP_SIZE + SW_SIZE);\n','')
assert restored==function(old,'cap_init'),'reservation-only cap_init extension'
wq=(K/'kernel/workqueue.c').read_text();basewq=(B/'kernel/kernel/workqueue.c').read_text();hook=(R/'source/work-hook.inc').read_text().rstrip('\n')
assert wq.replace('#include <linux/asus_retained_trace.h>\n','',1).replace('\tu64 dispatch_token;\n','',1).replace(hook,'\tworker->current_func(work);',1)==basewq
f=function(wq,'process_one_work');assert f.index('spin_unlock_irq(&pool->lock);')<f.index('lock_map_acquire_read(')<f.index('trace_workqueue_execute_start(work);')<f.index('asus_capture_work_enter(')<f.index('worker->current_func(work);')<f.index('asus_capture_work_return(dispatch_token);')<f.index('trace_workqueue_execute_end(work);')<f.index('lock_map_release(')<f.index('spin_lock_irq(&pool->lock);')
assert 'asus_capture_work_return(dispatch_token);' in hook and hook.count('work)')==2
nm=subprocess.check_output(['aarch64-linux-gnu-nm','-S','--defined-only',str(O/'vmlinux')],text=True)
sized={p[3]:(int(p[0],16),int(p[1],16)) for l in nm.splitlines() if len(p:=l.split())==4}
sym={n:a for n,(a,s) in sized.items()}
for l in subprocess.check_output(['aarch64-linux-gnu-nm','-an',str(O/'vmlinux')],text=True).splitlines():
 p=l.split()
 if len(p)==3:sym[p[2]]=int(p[0],16)
def dump(o,a,z):return subprocess.check_output(['aarch64-linux-gnu-objdump','-d','--start-address='+hex(a),'--stop-address='+hex(a+z),str(o/'vmlinux')],text=True)
init_addr,init_size=sized['asus_retained_trace_init'];init_dis=dump(O,init_addr,init_size);rec_init=int(re.search(r'\bbl\s+([0-9a-f]+) <trace_init>',init_dis).group(1),16)
sized['trace_init']=next((int(p[0],16),int(p[1],16)) for l in nm.splitlines() if len(p:=l.split())==4 and p[3]=='trace_init' and int(p[0],16)==rec_init)
names=['process_one_work','asus_capture_work_enter','asus_capture_work_return','finish_task_switch','asus_capture_switch','__clean_dcache_area_poc','_raw_spin_trylock','_raw_spin_unlock_irqrestore','ktime_get_ts64','arch_counter_read','asus_retained_trace_init','trace_init','cap_init']
names += [n for n in sized if n.split('.')[0] in ['wd_record','wd_header','wd_init','wd_fault','sw_commit'] or n.startswith('arch_timer_handler_')]
dis={n:dump(O,*sized[n]) for n in names if n in sized and sized[n][1]}
(E/'scoped-hooks.disasm').write_text('\n'.join(dis.values()))
# Save exact base seam for local before/after inspection; no vmlinux leaves VM.
basenm=subprocess.check_output(['aarch64-linux-gnu-nm','-S','--defined-only',str(B/'out/vmlinux')],text=True)
baseinfo=next((int(p[0],16),int(p[1],16)) for l in basenm.splitlines() if len(p:=l.split())==4 and p[3]=='process_one_work')
(E/'base-process_one_work.disasm').write_text(dump(B/'out',*baseinfo))
pw=dis['process_one_work'];enter=pw.index('<asus_capture_work_enter>');ret=pw.index('<asus_capture_work_return>');call=re.search(r'\bblr\s+x\d+',pw[enter:ret]);assert call and len(re.findall(r'\bblr\b',pw[enter:ret]))==1
assert not re.search(r'\b(?:bl|msr)\b',pw[enter+len('<asus_capture_work_enter>'):enter+call.start()]),'no intervening calls/IRQ write before original indirect call'
assert not re.search(r'\b(?:bl|msr)\b',pw[enter+call.end():ret].rsplit('\n',1)[0]),'no intervening calls/IRQ writes before postcall'
record=next(v for n,v in dis.items() if n.split('.')[0]=='wd_record')
assert len(re.findall(r'\bmrs\s+x\d+, cntvct_el0',record))==1 and not re.search(r'\bblr\b',record)
rec={n:v for n,v in dis.items() if n.startswith('wd_') or n.startswith('asus_capture_work_')}
calls={n:sorted(set(re.findall(r'\b(?:bl|b)\s+[0-9a-f]+ <([^>]+)>',v))) for n,v in rec.items()}
for n,targets in calls.items():
 for t in targets:assert t.split('+')[0] in ['__clean_dcache_area_poc','memcpy','memcmp','memset','__memset','__memcpy','__memcmp','cap_hex','__stack_chk_fail','_raw_spin_trylock','_raw_spin_unlock_irqrestore','sw_commit'] or t.startswith(('wd_','asus_capture_work_')),(n,t)
assert '<asus_capture_switch>' in dis['finish_task_switch'] and '<kthread_data>' in dis['finish_task_switch']
assert '<asus_capture_mono_enter>' in dis['ktime_get_ts64'] and '<asus_capture_exit>' in dis['ktime_get_ts64']
assert '<asus_capture_counter_enter>' in dis['arch_counter_read'] and '<asus_capture_exit>' in dis['arch_counter_read']
handlers={n:v for n,v in dis.items() if n.startswith('arch_timer_handler_')};assert handlers and all('<asus_capture_event_enter>' in v and '<asus_capture_exit>' in v for v in handlers.values())
assert re.search(r'\bdsb\s+sy',dis['__clean_dcache_area_poc'])
assert '#0x3b3f' in dis['trace_init'], 'actual 15168-byte OEM capacity reservation missing'
assert '<_raw_spin_unlock_irqrestore>' in record and '<_raw_spin_trylock>' in record
raw=(O/'arch/arm64/boot/Image').read_bytes();identity=json.loads((R/'source/identity.json').read_text());text=sym['_text'];a,z=sym['asus_entry_tag'],sym['asus_entry_tag_end'];assert raw[a-text:z-text]==identity['tag'].encode()
for tag in ['A49CAP1','A49SW2','A49WD1']:assert (tag+' uuid='+identity['run_uuid']).encode() in raw
assert b'ASUS49-DIAG headless RDMA IRQ registration skipped' in raw
image_size=struct.unpack_from('<Q',raw,16)[0];assert image_size==sym['_end']-text and image_size>=len(raw)
def ungzip(p):
 d=zlib.decompressobj(31);r=d.decompress(p);assert d.eof;return r,d.unused_data
_,dt=ungzip((O/'arch/arm64/boot/Image.gz-dtb').read_bytes());_,bdt=ungzip((B/'out/arch/arm64/boot/Image.gz-dtb').read_bytes());assert dt==bdt
assert sha(B/'out/arch/arm64/boot/Image.gz-dtb')==identity['base_compiled_sha256']
result=dict(status='PASS_SCOPED_SOURCE_AND_ACTUAL_ELF',entry_identity=identity,Image=dict(file_bytes=len(raw),image_size=image_size,text=hex(text),end=hex(sym['_end'])),preserved_sources=preserved,recorder_calls=calls,raw_CNTVCT_reads=1,indirect_recorder_calls=0,cache_clean_barrier='actual linked dsb sy',legacy_and_scheduler_capture_bodies_byte_identical=True,config_byte_identical=True,hardware_DTB_byte_identical=True,hardware_DTB_sha256=hashlib.sha256(dt).hexdigest(),compiler_stack_protector='inherited canary-failure-only __stack_chk_fail',seam='original process_one_work current_func(work), exact source expression retained; entry before call, token-only return before existing execute-end tracepoint',old_capture_area_bytes=9600,work_capture_area_bytes=5568,combined_bytes=15168,symbols={n:dict(address=hex(sized[n][0]),bytes=sized[n][1]) for n in names if n in sized},physical_execution=False)
(E/'linked-capture.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
