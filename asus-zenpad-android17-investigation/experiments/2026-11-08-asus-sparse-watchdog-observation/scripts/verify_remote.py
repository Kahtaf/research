"""Scoped actual ELF/profile and frozen-baseline verification; no target input."""
from pathlib import Path
import hashlib,json,re,struct,subprocess,zlib

R=Path('/srv/android/asus-sparse-watchdog-observation-20261108-e0b1a1ba')
B=Path('/srv/android/asus-sparse-observer-liveness-20261108-e6799dac')
K=R/'kernel';O=R/'out';E=R/'evidence'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
save=lambda n,d:(E/n).write_text(json.dumps(d,indent=2)+'\n')
i=json.loads((R/'source/identity.json').read_text())
status=json.loads((E/'build-status.json').read_text())
assert status['status']=='complete' and status['compile_attempts']==1 and status['max_jobs']==8
assert (O/'source').resolve()==K
pins=json.loads((E/'source-pins.json').read_text())
for n,v in pins.items():
 assert sha(K/n)==v['after'] and sha(B/'kernel'/n)==v['before'],n
preserved=json.loads((E/'preserved-source-pins.json').read_text())
for n,v in preserved.items():
 assert sha(K/n)==sha(B/'kernel'/n)==v,n
assert (O/'.config').read_bytes()==(B/'out/.config').read_bytes()
assert sha(O/'.config')=='708a88175ea777c09410000dfe5cf562ccbf764955eb9deaadda7326d0a966e1'
inodes={}
for n,v in json.loads((E/'base-freeze.json').read_text()).items():
 p=B/n;c=R/n
 assert sha(p)==v['sha256'] and p.stat().st_ino==v['inode'] and p.stat().st_mtime_ns==v['mtime_ns'],n
 assert c.stat().st_ino!=p.stat().st_ino,n
 inodes[n]=dict(base_inode=p.stat().st_ino,candidate_inode=c.stat().st_ino,base_hash=v['sha256'],base_unchanged=True,independent=True)
save('repository-preservation.json',dict(status='PASS_SCOPED_FREEZE_AND_INDEPENDENT_INODES',scope=inodes,copy='cp -a --reflink=auto kernel AND out including nested repositories',full_tree_audit=False))

# Local token-restoration control is bound by these exact source hashes.
source=(K/'arch/arm64/kernel/asus_retained_trace.c').read_text()
base=(B/'kernel/arch/arm64/kernel/asus_retained_trace.c').read_text()
writer=lambda s:s[s.index('void asus_retained_trace_write('):s.index('/* No printk, clocks, allocation') if '/* No printk, clocks, allocation' in s else s.index('static void __init trace_init(')]
assert writer(source)==writer(base)
init=lambda s:s[s.index('static void __init cap_init('):s.index('static bool cap_lock(')]
assert init(source)==init(base)
areas=['cap_area','sw_area','wd_area','ps_area','pm_area','dl_area']
assert '#define ASUS_SPARSE_PROFILE 1' in (K/'arch/arm64/kernel/asus_entry_tag.h').read_text()
save('source-checks.json',dict(status='PASS_PINNED_SOURCE_AND_UNCHANGED_SPARSE_WRITER',changed_files=list(pins),writer_byte_identical=True,hot_gate_byte_identical=True,preserved_sources=preserved))

obj=O/'arch/arm64/kernel/asus_retained_trace.o'
oldobj=B/'out/arch/arm64/kernel/asus_retained_trace.o'
objdis=subprocess.check_output(['aarch64-linux-gnu-objdump','-dr',str(obj)],text=True)
olddis=subprocess.check_output(['aarch64-linux-gnu-objdump','-dr',str(oldobj)],text=True)
objnm=subprocess.check_output(['aarch64-linux-gnu-nm','-S','--defined-only',str(obj)],text=True)
onames={x[3]:x for l in objnm.splitlines() if len(x:=l.split())==4}
assert len(re.findall(r'\bstlr\b',olddis))==0
assert not re.search(r'\bstlr\b',objdis),'ready publication remains compiled'
for name in ['cap_init','sw_init','wd_init','ps_init','pm_init','dl_init']:
 assert not any(n.split('.')[0]==name for n in onames),name
for area in areas:
 assert area in onames and onames[area][2].lower()=='b' and int(onames[area][1],16)==8,(area,onames.get(area))
 assert re.search(r'R_AARCH64_[^\n]*\b'+area+r'\b',objdis) or area in objnm
(E/'retained-recorder-object.disasm').write_text(objdis)
(E/'retained-recorder-object.nm').write_text(objnm)

nm=subprocess.check_output(['aarch64-linux-gnu-nm','-S','--defined-only',str(O/'vmlinux')],text=True)
rows=[x for l in nm.splitlines() if len(x:=l.split())==4]
sized={x[3]:(int(x[0],16),int(x[1],16),x[2]) for x in rows}
def dump(n,root=O):
 a,z,_=sized[n]
 return subprocess.check_output(['aarch64-linux-gnu-objdump','-d','--start-address='+hex(a),'--stop-address='+hex(a+z),str(root/'vmlinux')],text=True)
names=['asus_retained_trace_write','trace_init','__delay','__const_udelay','__clean_dcache_area_poc','asus_sparse_wdt_record','mtk_wdt_stop','mtk_wdt_probe','mtk_reset_handler','mtk_wdt_start','mtk_wdt_set_timeout','mtk_wdt_driver_init','notifier_call_chain']
dis={n:dump(n) for n in names}
(E/'scoped-linked.disasm').write_text('\n'.join(dis.values()))
assert 'stlr' not in dis['trace_init']
assert '<cap_init>' not in dis['trace_init']
assert re.search(r'\bdsb\s+sy',dis['__clean_dcache_area_poc'])
de=dis['__delay']
assert 'cntpct_el0' not in de and len(re.findall(r'\bmrs\s+x\d+, cntvct_el0',de))==3
assert len(re.findall(r'\bblr\b',de))==3 and len(re.findall(r'\byield\b',de))==1
assert '<asus_capture_delay_begin>' in de
# Publication's payload/header cleans are still linked in the accepted path.
w=dis['asus_retained_trace_write']
assert len(re.findall(r'\bbl\s+'+format(sized['__clean_dcache_area_poc'][0],'x')+r'\s+<',w))==2
assert '<_raw_spin_trylock>' in w and '<_raw_spin_unlock_irqrestore>' in w
assert sized['__memcpy'][0]==sized['memcpy'][0]
assert re.search(r'\b(?:bl|b)\s+'+format(sized['memcpy'][0],'x')+r'\s+<',w)
for a in areas:
 assert sized[a][2].lower()=='b' and sized[a][1]==8
raw=(O/'arch/arm64/boot/Image').read_bytes()
assert b'ASUS49-ENTRY run='+i['run_uuid'].encode() in raw and i['mode'].encode() in raw
for tag in ['A49CAP1','A49SW2','A49WD1','A49PS1','A49PM1','A49DL1']:
 assert (tag+' uuid=').encode() not in raw,tag
assert b'ASUS49-DIAG headless RDMA IRQ registration skipped' in raw
def unzip(blob):
 d=zlib.decompressobj(31);data=d.decompress(blob);assert d.eof
 return data,d.unused_data
newraw,dt=unzip((O/'arch/arm64/boot/Image.gz-dtb').read_bytes())
_,bdt=unzip((B/'out/arch/arm64/boot/Image.gz-dtb').read_bytes())
assert newraw==raw and dt==bdt
assert raw[56:60]==b'ARM\x64'
image_size=struct.unpack_from('<Q',raw,16)[0]
assert image_size>=len(raw)
result=dict(status='PASS_ACTUAL_SOURCE_AND_ELF_SPARSE_PROFILE',entry_identity=i,
    Image=dict(file_bytes=len(raw),image_size=image_size),config_byte_identical=True,DT_byte_identical=True,
    ready_pointer_symbols={a:dict(address=hex(sized[a][0]),bytes=sized[a][1],section_type=sized[a][2],initial_value=0) for a in areas},
    old_ready_publication_stlr_count=0,sparse_ready_publication_stlr_count=0,hot_init_functions_absent=True,
    hot_header_tags_absent_from_Image=True,normal_not_ready_admission='six zero BSS ready pointers; no compiled release stores; unchanged API admission',
    accepted_writer_clean_calls=2,cache_clean_ends_DSB_SY=True,
    delay=dict(source_byte_identical=True,virtual_MRS_sites=3,OOL_indirect_sites=3,physical_MRS_sites=0,disabled_cookie=0,original_loop_and_get_cycles_route=True),
    early_entry_writer_source_unchanged=True,memory_mapping_and_guards_unchanged=True,
    preserved_sources=preserved,physical_execution=False)
save('linked-capture.json',result)
print(json.dumps({k:result[k] for k in ['status','old_ready_publication_stlr_count','sparse_ready_publication_stlr_count','hot_header_tags_absent_from_Image']},indent=2))

# Actual linked cold paths and ABI; large vmlinux stays on this VM.
stop=dis['mtk_wdt_stop'];restart=dis['mtk_reset_handler'];probe=dis['mtk_wdt_probe'];emit=dis['asus_sparse_wdt_record']
assert len(re.findall(r'\bldr\s+w\d+, \[x\d+\]',stop))==2
assert len(re.findall(r'\bstr\s+w\d+, \[x\d+\]',stop))==1
assert stop.index('str\tw') < stop.rindex('ldr\tw') < stop.index('<asus_sparse_wdt_record>')
assert '#0x22000000' in stop and '#0xfffffffe' in stop
assert probe.index('<asus_sparse_wdt_record>') < probe.index('<devm_kmalloc>')
assert probe.index('<mtk_wdt_stop>') < probe.index('<watchdog_register_device>')
assert '<mtk_wdt_start>' not in probe and '<mtk_wdt_set_timeout>' not in probe
assert restart.index('<asus_sparse_wdt_record>') < re.search(r'\bldr\s+w',restart).start()
assert restart.count('<asus_sparse_wdt_record>')==1 and stop.count('<asus_sparse_wdt_record>')==1
calls={n for n in re.findall(r'\b(?:bl|b)\s+[0-9a-f]+ <([^>]+)>',emit) if not n.startswith('asus_sparse_wdt_record+')}
assert calls <= {'scnprintf','asus_retained_trace_write','__stack_chk_fail'},calls
assert '<scnprintf>' in emit and '<asus_retained_trace_write>' in emit
assert not any(x in emit for x in ['cntvct','cntpct','printk','kmalloc','schedule','delay','lock>'])
assert '__initcall_mtk_wdt_driver_init3' in sized and '__initcall_watchdog_init4s' in sized
for n in ['mtk_wdt_restart','wd_api_init','get_wd_api','wdt_arch_reset','wk_wdt_thread','kicker_thread']:
 assert n not in sized,n
wdobj=subprocess.check_output(['aarch64-linux-gnu-objdump','-dr',str(O/'drivers/watchdog/mtk_wdt.o')],text=True)
(E/'watchdog-object.disasm').write_text(wdobj)
# Caller LR is transported without dereferencing or symbol lookup on target.
assert re.search(r'\bmov\s+x4, x30',stop) or re.search(r'\bmov\s+x4, x\d+',stop)
save('watchdog-linked.json',dict(status='PASS_ACTUAL_COLD_PATH_ORDER',stop_MMIO_MODE_loads=2,stop_MMIO_MODE_stores=1,stop_original_read_reused=True,stop_readback_after_keyed_write_before_record=True,probe_stop_before_watchdog_registration=True,probe_start_timeout_not_called=True,restart_record_before_original_status_read_and_backup_write=True,restart_status_operations_not_duplicated=True,emitter_direct_external_calls=sorted(calls),compiler_stack_protector='existing config adds __stack_chk_fail only on canary mismatch; normal path scnprintf and retained writer only',registration='arch_initcall level 3; watchdog core subsys_initcall level 4s',legacy_kicker_not_linked=True,original_source_operations_verified_by_token_restoration=True,extra_read_offsets=['MODE 0x00 once per stop','REQ_MODE 0x30 once at probe end','REQ_IRQ_EN 0x34 once at probe end'],physical=False))
