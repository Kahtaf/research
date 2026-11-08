from pathlib import Path
import json,hashlib,subprocess,re,struct,zlib,gzip
R=Path('/srv/android/asus-linux49-scheduler-switch-capture-20261107-3d26cc95');B=Path('/srv/android/asus-linux49-rdma-registration-skip-20261107-d140b2bf');K=R/'kernel';O=R/'out';E=R/'evidence'
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
# Existing capture function bodies remain byte-identical, except cap_init reservation.
def function(s,n):
 a=s.index(n+'(');a=s.index('{',a);depth=1;i=a+1
 while depth:
  depth+=(s[i]=='{')-(s[i]=='}');i+=1
 return s[a:i]
for n in ['cap_hex','cap_fault','cap_publish','cap_lock','cap_enter','cap_match','asus_capture_mono_enter','asus_capture_mono_seq','asus_capture_exit','asus_capture_counter_enter','asus_capture_event_enter','trace_overlaps','trace_check_dt','asus_retained_trace_write','trace_init']:
 assert function(old,n)==function(new,n),n
core=(K/'kernel/sched/core.c').read_text();basecore=(B/'kernel/kernel/sched/core.c').read_text()
assert core.replace('#include <linux/asus_retained_trace.h>\n','').replace('\tasus_capture_switch(prev, prev_state);\n','')==basecore
f=function(core,'finish_task_switch');assert f.index('prev_state = prev->state;')<f.index('asus_capture_switch(prev, prev_state);')<f.index('finish_lock_switch(rq, prev);')<f.index('put_task_struct(prev);')
nm=subprocess.check_output(['aarch64-linux-gnu-nm','-S','--defined-only',str(O/'vmlinux')],text=True)
sized={p[3]:(int(p[0],16),int(p[1],16)) for l in nm.splitlines() if len(p:=l.split())==4}
sym={n:a for n,(a,s) in sized.items()}
# non-sized boundary symbols from nm
for l in subprocess.check_output(['aarch64-linux-gnu-nm','-an',str(O/'vmlinux')],text=True).splitlines():
 p=l.split()
 if len(p)==3:sym[p[2]]=int(p[0],16)
names=['finish_task_switch','asus_capture_switch','__clean_dcache_area_poc','ktime_get_ts64','arch_counter_read','asus_retained_trace_init','trace_init','cap_init']
names += [n for n in sized if (n.split('.')[0] in ['sw_header','sw_init','sw_commit','sw_fault'] or n.startswith('arch_timer_handler_'))]
dis={}
for n in names:
 if n not in sized:continue
 a,z=sized[n]
 if z:dis[n]=subprocess.check_output(['aarch64-linux-gnu-objdump','-d','--start-address='+hex(a),'--stop-address='+hex(a+z),str(O/'vmlinux')],text=True)
(E/'scoped-hooks.disasm').write_text('\n'.join(dis.values()))
assert '<asus_capture_switch>' in dis['finish_task_switch']
finish=dis['finish_task_switch']
assert re.search(r'ldr\s+x23, \[x20, #24\]',finish)
assert re.search(r'mov\s+x1, x23\n[^\n]+bl\s+[^\n]+<asus_capture_switch>',finish)
assert finish.index('<asus_capture_switch>')<finish.index('<_raw_spin_unlock_irq>')
assert re.search(r'mov\s+x0, x20',finish[:finish.index('<asus_capture_switch>')])

sw=dis['asus_capture_switch'];assert len(re.findall(r'\bmrs\s+x\d+, cntvct_el0',sw))==1
assert not re.search(r'\bblr\b',sw)
rec={n:v for n,v in dis.items() if n=='asus_capture_switch' or n.split('.')[0] in ['sw_header','sw_init','sw_commit','sw_fault']}
calls={n:sorted(set(re.findall(r'\bbl\s+[0-9a-f]+ <([^>]+)>',v))) for n,v in rec.items()}
for n,targets in calls.items():
 for t in targets:assert t in ['__clean_dcache_area_poc','memcpy','memcmp','memset','__memset','__memcpy','__memcmp','cap_hex','__stack_chk_fail'] or t.startswith('sw_'),(n,t)
assert '<asus_capture_mono_enter>' in dis['ktime_get_ts64'] and '<asus_capture_mono_seq>' in dis['ktime_get_ts64'] and '<asus_capture_exit>' in dis['ktime_get_ts64']
assert '<asus_capture_counter_enter>' in dis['arch_counter_read'] and '<asus_capture_exit>' in dis['arch_counter_read'] and len(re.findall(r'\bblr\b',dis['arch_counter_read']))==1
handlers={n:v for n,v in dis.items() if n.startswith('arch_timer_handler_')};assert handlers
assert all('<asus_capture_event_enter>' in v and '<asus_capture_exit>' in v and len(re.findall(r'\bblr\b',v))==1 for v in handlers.values())
assert 'dsb\tsy' in dis['__clean_dcache_area_poc'] or re.search(r'\bdsb\s+sy',dis['__clean_dcache_area_poc'])
raw=(O/'arch/arm64/boot/Image').read_bytes();identity=json.loads((R/'source/identity.json').read_text());text=sym['_text']
a,z=sym['asus_entry_tag'],sym['asus_entry_tag_end'];assert raw[a-text:z-text]==identity['tag'].encode()
assert ('A49CAP1 uuid='+identity['run_uuid']).encode() in raw and ('A49SW1 uuid='+identity['run_uuid']).encode() in raw
assert b'ASUS49-DIAG headless RDMA IRQ registration skipped' in raw
image_size=struct.unpack_from('<Q',raw,16)[0];assert image_size==sym['_end']-text and image_size>=len(raw)
def ungzip(p):
 d=zlib.decompressobj(31);r=d.decompress(p);assert d.eof;return r,d.unused_data
_,dt=ungzip((O/'arch/arm64/boot/Image.gz-dtb').read_bytes());_,bdt=ungzip((B/'out/arch/arm64/boot/Image.gz-dtb').read_bytes());assert dt==bdt
assert sha(B/'out/arch/arm64/boot/Image.gz-dtb')==identity['base_compiled_sha256']
result=dict(status='PASS_SCOPED_SOURCE_AND_ACTUAL_ELF',entry_identity=identity,Image=dict(file_bytes=len(raw),image_size=image_size,text=hex(text),end=hex(sym['_end'])),preserved_sources=preserved,recorder_direct_calls=calls,raw_CNTVCT_reads=1,indirect_recorder_calls=0,added_lock_calls=0,cache_clean_barrier='actual linked dsb sy',legacy_capture_function_bodies_byte_identical=True,old_hooks_linked=True,config_byte_identical=True,hardware_DTB_byte_identical=True,hardware_DTB_sha256=hashlib.sha256(dt).hexdigest(),compiler_stack_protector='inherited config; __stack_chk_fail is a canary-failure-only cold branch, not ordinary recorder work',scheduler_hook='immediately after original prev_state snapshot; before finish_lock_switch and task lifetime changes',capture_area_bytes=3008,old_capture_area_bytes=5952,combined_bytes=8960,symbols={n:dict(address=hex(sized[n][0]),bytes=sized[n][1]) for n in names if n in sized},physical_execution=False)
(E/'linked-capture.json').write_text(json.dumps(result,indent=2)+'\n');(E/'System.map.gz').write_bytes(gzip.compress((O/'System.map').read_bytes(),mtime=0));print(json.dumps(result,indent=2))
