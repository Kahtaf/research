"""Focused real-artifact preservation/linkage and synthetic decoder controls."""
from pathlib import Path
import gzip,hashlib,importlib.util,json,re,struct,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[1];S=R/'source';E=R/'evidence'
sys.path.insert(0,str(S));import bootformat as b
spec=importlib.util.spec_from_file_location('boundary_decoder',R/'scripts/decode_boundary.py');d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
I=json.loads((E/'identity.json').read_text());P=json.loads((E/'packaging-receipt.json').read_text());build=json.loads((E/'build-receipt.json').read_text())
checks={}
def check(name,yes):assert yes,name;checks[name]=True
def fun(s,name):
 start=s.index(name+'(');a=s.index('{',start);depth=1;j=a+1
 while depth:
  depth+=(s[j]=='{')-(s[j]=='}');j+=1
 return s[a:j]
base=(S/'base/kernel/printk/printk.c').read_text();new=(S/'kernel/printk/printk.c').read_text();ret=(S/'arch/arm64/kernel/asus_retained_trace.c').read_text();oldret=(S/'base/arch/arm64/kernel/asus_retained_trace.c').read_text()
check('existing_log_store_entire_function_identical',fun(base,'log_store')==fun(new,'log_store'))
check('direct_writer_entire_function_identical',fun(ret,'asus_retained_trace_write')==fun(oldret,'asus_retained_trace_write'))
check('trace_initialization_and_hot_disable_identical',fun(ret,'trace_init')==fun(oldret,'trace_init') and fun(ret,'cap_init')==fun(oldret,'cap_init'))
f=fun(new,'devkmsg_write');bf=fun(base,'devkmsg_write')
check('original_validity_and_ratelimit_prefix_identical',f[:f.index('write_seq =')].replace('\n\tu32 write_seq;','')==bf[:bf.index('buf = kmalloc')])
# Erase only the four new calls, their conditional guards and added error braces;
# the original devkmsg body must then be exact, including copy/free/return order.
restored=f.replace('\n\tu32 write_seq;','').replace('\twrite_seq = asus_devkmsg_boundary(0, len, 0);\n','')
restored=re.sub(r'\t(?:\t)?if \(write_seq\)\n\t(?:\t)?\tasus_devkmsg_boundary\(write_seq, ret, (?:-ENOMEM|-EFAULT|ret)\);\n','',restored)
restored=restored.replace('if (buf == NULL) {\n\t\treturn -ENOMEM;\n\t}','if (buf == NULL)\n\t\treturn -ENOMEM;')
check('original_devkmsg_operations_exact_after_removing_hooks',restored==bf)
emit=fun(ret,'asus_devkmsg_boundary')
check('cold_pid1_only_no_outer_lock_irq_clock_allocation', 'current->pid != 1 || !in_task()' in emit and not re.search(r'printk\(|kmalloc\(|kfree\(|copy_from|local_clock\(|ktime|ioread|writel|spin_|irq_save|irq_disable',emit))
check('bounded_stack_and_admission_budget', 'char line[160]' in emit and 'writes >= 768' in emit and 'UNKNOWN reason=write-budget limit=768' in emit and 'return 0;' in emit)
for n,pins in json.loads((E/'prepost.json').read_text()).items():
 check('exact_source_pin_'+n,hashlib.sha256((S/'base'/n).read_bytes()).hexdigest()==pins['before'] and hashlib.sha256((S/n).read_bytes()).hexdigest()==pins['after'])
linked=(E/'linked-devkmsg_write.disasm').read_text();em=(E/'linked-asus_devkmsg_boundary.disasm').read_text();log=(E/'linked-log_store.disasm').read_text()
check('linked_four_boundary_calls_and_actual_alloc_copy_emit_free',len(re.findall(r'\bbl\s+[0-9a-f]+ <asus_devkmsg_boundary>',linked))==4 and all('<'+s+'>' in linked for s in ['__kmalloc','copy_from_iter','printk_emit','kfree']))
check('linked_emitter_only_formatter_writer_stack_guard_calls',set(re.findall(r'\bbl\s+[0-9a-f]+ <([^>]+)>',em))=={'scnprintf','asus_retained_trace_write','__stack_chk_fail'})
clock_tail=log[log.index('<sched_clock>'):];back=re.search(r'\bb\s+([0-9a-f]+) <log_store',clock_tail)
writer_call=re.search(r'([0-9a-f]+):[^\n]*\bbl\s+[0-9a-f]+ <asus_retained_trace_write>',log)
check('linked_LOG_after_inlined_local_clock_sched_clock_return',bool(back and writer_call and int(back[1],16)<int(writer_call[1],16) and re.search(r'str\s+x0, \[x26\]',clock_tail)))
syms=json.loads((E/'linked-route-symbols.json').read_text());blob=bytearray()
for line in (E/'linked-kmsg-fops.txt').read_text().splitlines():
 m=re.match(r' [0-9a-f]+ ((?:[0-9a-f]{8} ){1,4})',line)
 if m:blob.extend(bytes.fromhex(m[1]))
# file_operations: owner,llseek,read,write,read_iter,write_iter => offset40.
check('actual_linked_kmsg_fops_write_iter_points_to_instrumented_devkmsg',len(blob)>=48 and struct.unpack_from('<Q',blob,40)[0]==int(syms['devkmsg_write']['address'],16))
mapdata=gzip.decompress((R/'artifacts/System.map.gz').read_bytes());mp=json.loads((E/'System.map-uncompressed.json').read_text())
check('genuine_System_map_gzip_and_uncompressed_pin',len(mapdata)==mp['bytes'] and hashlib.sha256(mapdata).hexdigest()==mp['sha256']==build['artifacts']['System.map']['sha256'] and all((s+'\n').encode() in mapdata for s in ['devkmsg_write','asus_devkmsg_boundary','log_store']))
check('one_kernel_build_no_helper_compile_no_local_vmlinux',build['kernel_builds']==1 and build['helper_compiles']==0 and not (R/'artifacts/vmlinux').exists())
check('all_package_preservation_checks',all(P['preservation'][k] for k in P['preservation'] if k!='adapters'))
check('actual_config_pin',hashlib.sha256((R/'artifacts/resolved.config').read_bytes()).hexdigest()=='708a88175ea777c09410000dfe5cf562ccbf764955eb9deaadda7326d0a966e1')
check('one_isolated_PLAN_no_device_and_delivered_guard_unchanged',json.loads((E/'plan-isolation-receipt.json').read_text())['actual_installer_main_calls']==1 and json.loads((E/'install-plan.json').read_text())['device_contacted'] is False)
# Synthetic records, explicitly not physical evidence. Include filtered setup
# pairs, all calibration triples, and a signal-handler write between main writes.
def helper(tail):return d.HELPER+tail
cp=helper(' phase=observe stage=actual op=clock.path path=CLOCK_MONOTONIC rc=0 errno=0 value='+d.CLOCK_PATH)
ib=helper(' phase=observe stage=begin op=clock_gettime path=loop.initial rc=0 errno=0 value=-')
ie=helper(' phase=observe stage=end op=clock_gettime path=loop.initial rc=0 errno=0 value=0.642032768')
np=helper(' phase=observe stage=actual op=sched.original path=pid0 rc=0 errno=0 value=getparam_rc=0 getparam_errno=0 priority=0')
alarm=helper(d.ALARM)
def pair(seq,line=None,length=None,rc=None):
 n=length if length is not None else len(line.encode())+4
 return [d.PREFIX+f'WENT seq={seq} len={n}']+([line] if line else [])+[d.PREFIX+f'WRET seq={seq} len={n} rc={n if rc is None else rc}']
lines=[d.ENTRY,I['mode']]+pair(1,length=80)+pair(2,cp)+pair(3,ib)+pair(4,ie)+pair(5,alarm)+pair(6,np)
text='\n'.join(lines)+'\n';args=[P['full_p10']['sha256'],'synthetic-stock-reference','synthetic-complete-reference']
positive=d.decode(text,*args)
check('decoder_positive_calibration_filtered_pair_signal_separate',positive['status']=='CALIBRATED_BOUNDARY_FACTS_STOP' and len(positive['observed_boundaries'])==6 and positive['signal_handler_writes']==[dict(seq=5,line=lines.index(alarm),main_flow_inference=False)])
check('missing_initial_clock_LOG_cannot_calibrate',d.decode(text.replace(ie+'\n',''),*args)['status']=='BOUNDARY_FACTS_PENDING_CALIBRATION_OR_BINDING_STOP')
check('decoder_unbound_cannot_accept',d.decode(text)['status']=='BOUNDARY_FACTS_PENDING_CALIBRATION_OR_BINDING_STOP')
cases={
 'stale_kernel':text.replace(I['kernel_uuid'],'f53fadc2-5cd5-4c44-b5a3-7a65567c6935'),
 'stale_control':text.replace(I['control_uuid'],'00000000-0000-0000-0000-000000000000'),
 'wrong_format':text.replace(' v=1 ',' v=2 '),
 'sequence_gap':text.replace('seq=6','seq=7'),
 'duplicate_entry':text.replace(lines[2],lines[2]+'\n'+lines[2]),
 'mismatched_length':text.replace('WRET seq=1 len=80','WRET seq=1 len=81'),
 'bad_LOG_length':text.replace(ie,ie+'x'),
 'LOG_without_WENT':text.replace(lines[lines.index(ie)-1]+'\n',''),
 'LOG_without_WRET':text.replace(lines[-1]+'\n',''),
 'WENT_without_LOG_or_WRET':'\n'.join(lines[:-3])+ '\n'+lines[-3]+'\n',
 'unknown_marker':text+d.PREFIX+'UNKNOWN reason=write-budget limit=768\n',
 'torn_last_record':text[:-2],
 'interleaved_nested_entry':text.replace(ie,d.PREFIX+'WENT seq=5 len=40\n'+ie),
 'duplicate_LOG':text.replace(ie,ie+'\n'+ie),
 'impossible_original_rc':text.replace('WRET seq=1 len=80 rc=80','WRET seq=1 len=80 rc=-1'),
 'unknown_helper':text.replace(ie,ie.replace('op=clock_gettime','op=bogus')),
 'hot_marker':text+'A49CAP1 uuid='+I['kernel_uuid']+'\n',
 'bad_record_order':text.replace('WENT seq=1 len=80','WRET seq=1 len=80 rc=80',1),
}
negative={}
for name,t in cases.items():
 r=d.decode(t,*args);check('decoder_reject_'+name,r['status']=='UNKNOWN_STOP' and bool(r['errors']));negative[name]=dict(status=r['status'],errors=r['errors'])
check('decoder_reject_wrong_fullp10',d.decode(text,'0'*64,*args[1:])['status']=='UNKNOWN_STOP')
# Original ENOMEM/EFAULT exits are legal paired facts without LOG, no semantics
# borrowed from missing records. A WRET alone does not assert user resumption.
for rc in [-12,-14]:
 t='\n'.join(lines+pair(7,length=90,rc=rc))+'\n';rr=d.decode(t,*args)
 check('decoder_original_early_return_'+str(rc),rr['status']=='CALIBRATED_BOUNDARY_FACTS_STOP' and rr['observed_boundaries'][-1]['rc']==rc)
# Complete filtered pair may have no LOG. Trailing missing WRET preserves earlier
# calibration but leaves integrity and causal interpretation UNKNOWN.
partial=d.decode(cases['LOG_without_WRET'],*args)
check('calibration_separate_from_partial_tail',partial['calibration']['initial_clock']=='TRIPLE_OBSERVED' and partial['calibration']['normal_policy']=='UNKNOWN' and partial['observed_boundaries'][-1]['span']=='LOG_CAPTURED_WRET_UNKNOWN')
maxwent=d.PREFIX+'WENT seq=768 len=992';maxret=d.PREFIX+'WRET seq=768 len=992 rc=992';overflow=d.PREFIX+'UNKNOWN reason=write-budget limit=768'
check('formats_fit_bounded_160_byte_stack',max(len(x)+1 for x in [maxwent,maxret,overflow])<=160)
(E/'synthetic-positive-console.txt').write_text(text)
(E/'synthetic-decoder-results.json').write_text(json.dumps(dict(synthetic_not_physical=True,positive=positive,negative=negative,partial_tail=partial),indent=2)+'\n')
(E/'focused-checks.json').write_text(json.dumps(dict(status='PASS',checks=checks,count=len(checks),synthetic_controls_not_physical=True),indent=2)+'\n')
print(json.dumps(dict(status='PASS',meaningful_checks=len(checks),parser_negative_controls=len(cases),max_boundary_record_bytes_including_newline=max(len(maxwent),len(maxret))+1),indent=2))
