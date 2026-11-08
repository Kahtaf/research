from pathlib import Path
import ast,gzip,hashlib,importlib.util,json,re,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[1];S=R/'source';E=R/'evidence';B=R.parent/'2026-11-08-asus-devkmsg-return-boundary';checks={}
def check(n,v):assert v,n;checks[n]=True
def body(s,n):
 a=s.index(n+'(');a=s.index('{',a);j=a+1;depth=1
 while depth:depth+=(s[j]=='{')-(s[j]=='}');j+=1
 return s[a:j]
def insns(n):
 text=(E/('linked-'+n+'.disasm')).read_text();out={}
 for l in text.splitlines():
  m=re.match(r'([0-9a-f]+):\s+[0-9a-f]{8}\s+(.+)',l)
  if m:out[int(m[1],16)]=m[2]
 return out
p=json.loads((E/'packaging-receipt.json').read_text());build=json.loads((E/'build-receipt.json').read_text());i=json.loads((E/'identity.json').read_text())
for n,v in json.loads((E/'prepost.json').read_text()).items():check('prepost_'+n,hashlib.sha256((S/'base'/n).read_bytes()).hexdigest()==v['before'] and hashlib.sha256((S/n).read_bytes()).hexdigest()==v['after'])
w=insns('pwrap_wait_for_state');clock=insns('sched_clock');idle=insns('pwrap_is_fsm_idle');vld=insns('pwrap_is_fsm_vldclr')
back=[(a,x) for a,x in w.items() if re.match(r'b.ne\s+[0-9a-f]+ <pwrap_wait_for_state',x) and int(re.search(r'b.ne\s+([0-9a-f]+)',x)[1],16)<a]
check('single_finite_poll_backedge',len(back)==1)
end=back[0][0];start=int(re.search(r'b.ne\s+([0-9a-f]+)',back[0][1])[1],16);loop=[(a,x) for a,x in w.items() if start<=a<=end]
check('budget_actual_2_to_24',any('mov\tw22, #0x1000000' in x for x in w.values()))
check('backedge_consumes_local_budget',w[end-4].startswith('subs\tw22, w22, #0x1'))
check('normal_loop_no_global_stores',not any(re.match(r'(?:st|cas|ldxr)',x) for a,x in loop))
check('clock_before_readiness_before_decrement', '<sched_clock>' in loop[0][1] and any(x=='blr\tx23' for a,x in loop) and list(w).index(end-4)>list(w).index(next(a for a,x in loop if x=='blr\tx23')))
count=len(loop)+len(clock)+min(len(idle),len(vld))
check('candidate_minimum_instructions_support_budget',len(clock)==34 and len(loop)==12 and len(idle)==10 and len(vld)==11 and count==56 and count>=48)
check('final_readiness_before_fixed_record', w[end+4]=='mov\tx0, x21' and w[end+8]=='blr\tx23' and any('stlr' in x for x in w.values()))
check('record_start_and_existing_sample_registers',any('stp\tx20, x19' in x for x in w.values()) and any('mov\tx19, x0' in x for a,x in loop))
check('original_ETIMEDOUT_actual_minus_110',sum('#-110' in x for x in w.values())>=2)
check('no_publication_in_transport_loop',not any('scnprintf' in x or 'retained_trace_write' in x for x in w.values()))
pub=(E/'linked-asus_pwrap_backstop_publish.disasm').read_text();bat=(E/'linked-battery_get_property.disasm').read_text()
check('emitter_only_formatter_writer_stack_failure_calls',set(re.findall(r'\bbl\s+[0-9a-f]+ <([^>]+)>',pub))=={'scnprintf','asus_retained_trace_write','__stack_chk_fail'})
check('emitter_atomic_context_IRQ_and_acquire_guards',all(x in pub for x in ['sp_el0','daif','ldar','ldxr','stlxr']) and pub.index('daif')<pub.index('<scnprintf>'))
check('publish_after_actual_callback_preserves_return',bat.index('<asus_p00a_battery_get_property>')<bat.index('mov\tw19, w0')<bat.index('<asus_pwrap_backstop_publish>')<bat.index('mov\tw0, w19'))
for n in ['pwrap_read','pwrap_write']:
 text=(E/('linked-'+n+'.disasm')).read_text();check('native_wait_call_'+n,text.count('<pwrap_wait_for_state>')==(2 if n=='pwrap_read' else 1))
ret=(S/'arch/arm64/kernel/asus_retained_trace.c').read_text();old=(S/'base/arch/arm64/kernel/asus_retained_trace.c').read_text()
for n in ['asus_retained_trace_write','asus_devkmsg_boundary','trace_init','cap_init']:check('baseline_unchanged_'+n,body(ret,n)==body(old,n))
check('cold_devkmsg_printk_entire_source_untouched', (B/'source/kernel/printk/printk.c').is_file() and 'kernel/printk/printk.c' not in json.loads((E/'prepost.json').read_text()))
sys.path.insert(0,str(S));import bootformat as boot
_,_,ram,_=boot.parse_image((R/'artifacts/candidate.img').read_bytes());entries=boot.parse_cpio(boot.ungzip(ram[512:])[0]);helper=entries['init'][3]
check('frozen_helper_run_and_control_separately_verified',('ASUS49-SYSCLOCK run='+i['helper_uuid']).encode() in helper and ('control='+i['control_uuid']).encode() in helper and hashlib.sha256(helper).hexdigest()=='9e9db33d3bf4615892ce40fe62bdaeb4f0240e2ebd6dabba81f565cff2ab2a1b')
check('frozen_components_package',all(v for k,v in p['preservation'].items() if k!='adapters'))
check('config_exact',hashlib.sha256((R/'artifacts/resolved.config').read_bytes()).hexdigest()=='708a88175ea777c09410000dfe5cf562ccbf764955eb9deaadda7326d0a966e1')
m=gzip.decompress((R/'artifacts/System.map.gz').read_bytes());mp=json.loads((E/'System.map-uncompressed.json').read_text());check('genuine_map_gzip_and_uncompressed_pin',len(m)==mp['bytes'] and hashlib.sha256(m).hexdigest()==mp['sha256']==build['artifacts']['System.map']['sha256'])
check('one_build_zero_helper_vmlinux_remote',build['kernel_builds']==1 and build['helper_compiles']==0 and not (R/'artifacts/vmlinux').exists())
check('isolated_actual_PLAN_once',json.loads((E/'plan-isolation-receipt.json').read_text())['actual_installer_main_calls']==1 and json.loads((E/'install-plan.json').read_text())['device_contacted'] is False)
spec=importlib.util.spec_from_file_location('decoder',R/'scripts/decode_boundary.py');d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
# Only new-contract controls. These bytes are synthetic, never a physical pass.
record=d.PWRAP+'EXHAUST start=100 last=99 iterations=16777216 wait=2 ready=0 rc=-110'
text='\n'.join([d.ENTRY,i['mode'],record])+'\n';args=[p['full_p10']['sha256'],'synthetic-fresh-reference','synthetic-complete-reference']
def pair(seq,line):
 n=len(line.encode())+4
 return [d.PREFIX+f'WENT seq={seq} len={n}',line,d.PREFIX+f'WRET seq={seq} len={n} rc={n}']
cal=[d.HELPER+' phase=observe stage=actual op=clock.path path=CLOCK_MONOTONIC rc=0 errno=0 value='+d.CLOCK_PATH,d.HELPER+' phase=observe stage=begin op=clock_gettime path=loop.initial rc=0 errno=0 value=-',d.HELPER+' phase=observe stage=end op=clock_gettime path=loop.initial rc=0 errno=0 value=0.642444769',d.HELPER+' phase=observe stage=actual op=sched.original path=pid0 rc=0 errno=0 value=getparam_rc=0 getparam_errno=0 priority=0']
caltext='\n'.join([d.ENTRY,i['mode'],record]+[line for seq,t in enumerate(cal,1) for line in pair(seq,t)])+'\n'
r=d.decode(caltext,*args);check('parser_synthetic_calibration_with_exact_frozen_identities_and_record',r['status']=='CALIBRATED_BOUNDARY_FACTS_STOP' and r['pwrap_backstop']['status']=='EXHAUSTION_RECORD_CAPTURED')
r=d.decode(text,*args)
check('parser_valid_record_separate_from_missing_calibration',not r['errors'] and r['status']!='CALIBRATED_BOUNDARY_FACTS_STOP' and r['pwrap_backstop']['records'][0]['captured_sample_delta_ns']==-1)
r=d.decode('\n'.join([d.ENTRY,i['mode']])+'\n',*args);check('no_record_stays_unknown',r['pwrap_backstop']['status']=='NOT_OBSERVED_UNKNOWN' and r['status']!='CALIBRATED_BOUNDARY_FACTS_STOP')
for name,t in [('duplicate',text+record+'\n'),('invalid_result',text.replace('ready=0 rc=-110','ready=1 rc=-110')),('stockproc_preamble','stockproc preamble line1\nstockproc preamble line2\n'+text)]:check('parser_refuses_'+name,d.decode(t,*args)['status']=='UNKNOWN_STOP' and bool(d.decode(t,*args)['errors']))
(E/'candidate-instruction-proof.json').write_text(json.dumps(dict(loop_start=hex(start),loop_end=hex(end),loop_instructions=len(loop),sched_clock_minimum_instructions=len(clock),idle_instructions=len(idle),WFVLDCLR_instructions=len(vld),selected_minimum_total=count,derivation_floor=48,reader_instructions_and_all_stalls_omitted=True),indent=2)+'\n')
(E/'focused-checks.json').write_text(json.dumps(dict(passed=True,checks=checks,parser_inputs='synthetic only; no target/private logs',physical_trial=False),indent=2)+'\n');print(json.dumps(dict(passed=True,checks=len(checks),candidate_min_instructions=count)))
