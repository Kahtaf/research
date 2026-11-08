from pathlib import Path
import json,re,gzip,hashlib
R=Path(__file__).resolve().parents[1];E=R/'evidence';s=(E/'scoped-hooks.disasm').read_text();linked=json.loads((E/'linked-capture.json').read_text())
def dis(n):
 t=s[s.index('<'+n+'>:'):];return t[:t.index('\n\n')]
f=dis('finish_task_switch');sw=dis('asus_capture_switch');h=dis('sw_header');k=dis('kthread_data');init=dis('trace_init')
checks=[r'mrs\s+x0, sp_el0',r'ldr\s+x23, \[x20, #24\]',r'mov\s+x0, x20\n[^\n]+mov\s+x1, x23\n[^\n]+bl\s+[^\n]+<asus_capture_switch>',r'ldr\s+x2, \[x0, #24\]',r'ldr\s+x3, \[x0, #16\]',r'orr\s+w4, w4, #0x2',r'ubfx\s+x4, x4, #5, #1',r'cbz\s+x0, [^\n]+<finish_task_switch\+0x144>',r'mrs\s+x0, daif',r'tbz\s+w0, #7',r'tbnz\s+w1, #5',r'cmp\s+w0, #0x1',r'cbnz\s+w0, [^\n]+<finish_task_switch\+0x58>']
for p in checks:assert re.search(p,f),p
assert f.index('<asus_capture_switch>')<f.index('stlr\tw0, [x1]')<f.index('<_raw_spin_unlock_irq>')
assert re.search(r'ldr\s+x0, \[x0, #1488\]',k) and re.search(r'ldur\s+x0, \[x0, #-40\]',k)
assert not re.search(r'\b(?:msr|blr)\b',sw+h+k)
# Exact actual register-to-array ABI: f[] starts sp+8, f[11..13] occupy +96,+104,+112.
for p in [r'mov\s+x6, x2',r'stp\s+x7, x6, \[sp, #88\]',r'stp\s+x3, x4, \[sp, #104\]',r'mov\s+w4, w4']:
 assert re.search(p,sw),p
for p in [r'ldp\s+w2, w0, \[x19, #56\]',r'cmp\s+w21, w0',r'sub\s+w0, w0, w21',r'mov\s+w1, #0x257f',r'cmp\s+w0, w1',r'b.ls\s+[^\n]+<trace_init\+0x4fc>',r'mov\s+w25, #0x2580',r'str\s+w21, \[x19, #56\]',r'stlr\s+x23, \[x0\]']:
 assert re.search(p,init),p
assert init.index('#0x257f')<init.index('<sw_init>')<init.index('str\tw21, [x19, #56]')<init.index('stlr\tx23, [x0]')
# Reservation body and all actual source/context invariants are unchanged outside the declared hook.
def body(s,n):
 a=s.index(n+'(');a=s.index('{',a);d=1;z=a+1
 while d:d+=(s[z]=='{')-(s[z]=='}');z+=1
 return s[a:z]
n='arch/arm64/kernel/asus_retained_trace.c';old=(R/'source/base'/n).read_text();new=(R/'source'/n).read_text();assert body(old,'cap_init')==body(new,'cap_init')
mapraw=gzip.decompress((R/'artifacts/System.map.gz').read_bytes());build=json.loads((E/'build-receipt.json').read_text());assert hashlib.sha256(mapraw).hexdigest()==build['artifacts']['System.map']['sha256']
abi=dict(status='PASS',physical_verified=False,source_safe_point='Original saved prev_state; added block and recorder before vtime/perf, prev on_cpu clear and rq unlock/lifetime changes',finish_task_switch_address=linked['symbols']['finish_task_switch']['address'],offsets=dict(saved_prev_state_load='0x4c',recorder_call='0x6c',current_SP_EL0_for_worker='0x110',PF_flag_snapshot='0x128',PF_bit_extract='0x130',kthread_data_call='0x244',current_func_load='0x250',current_work_load='0x258',prev_on_cpu_clear='0xa0',original_rq_unlock_call='0xa8'),ABI=dict(x0='prev retained in x20',x1='exact saved prev_state retained in x23 and later TASK_DEAD test',x2='READ_ONCE own worker+24 current_func',x3='READ_ONCE own worker+16 current_work',w4='bit0 PF_WQ_WORKER, bit1 own worker present',kthread_data='actual current from mrs SP_EL0; two loads task+1488(vfork_done), completion-40(data), return; no calls',recorder_new_fields='x2->x6->f[11] at sp+96; x3->f[12] at sp+104; zero-extended w4->f[13] at sp+112; numeric only, no pointer dereference'),worker_struct_layout='Exact branch union occupies16 bytes on64-bit; current_work+16, current_func+24; linked instructions load each exactly once after own worker NULL check',admission='Both seam and recorder check actual nr_cpu_ids1/CPU0/IRQs off/task context; recorder additionally readiness/guard/busy/overflow',new_worker_path_calls=['kthread_data'],no_added_locks_or_IRQmask_writes_or_faultable_helpers=True,recorder_stack_bytes=544,metadata_writer_stack_bytes=320,recorder=linked['symbols']['asus_capture_switch'],raw_counter='one unchanged isb+mrs cntvct_el0 in recorder; no new clock call',normal_recorder_calls=linked['recorder_direct_calls'],stack_guard='Inherited __stack_chk_fail canary-failure-only branch',cache_clean='Actual dsb sy',reservation=dict(body_byte_identical_to_base=True,actual_init_address=linked['symbols']['trace_init']['address'],combined_bytes=9600,load_logsize_and_capacity='ldp w2,w0,[header+56]',bounds='aligned pos<=actual sz_console; (sz_console-pos)>9599 before capture writes',publication='sw_init; clean combined; store log_size pos+9600; clean header; release-publish readiness'),local_System_map_uncompressed_verified=True)
(E/'hook-abi.json').write_text(json.dumps(abi,indent=2)+'\n');print(json.dumps(abi,indent=2))
