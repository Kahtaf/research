"""Offline boundary facts only. Binding arguments are parent attestations, not file reads."""
from pathlib import Path
import argparse,json,re
R=Path(__file__).resolve().parents[1]
I=json.loads((R/'evidence/identity.json').read_text())
BUEV='ASUS49-BUEV run='+I['kernel_uuid']+' v=1 '
SKIP=re.compile(re.escape(BUEV)+r'SKIP first=(0|[1-9][0-9]{0,9}) before=(0|[1-9][0-9]{0,9}) after=(0|[1-9][0-9]{0,9}) same_task=1 uevent_rc=(0|-?[1-9][0-9]{0,9})')
PWRAP='ASUS49-PWRAP run='+I['kernel_uuid']+' v=1 '
BUDGET=re.compile(re.escape(PWRAP)+r'EXHAUST start=(0|[1-9][0-9]{0,19}) last=(0|[1-9][0-9]{0,19}) iterations=16777216 wait=([012]) ready=([01]) rc=(0|-110)')
PREFIX='ASUS49-KMSG run='+I['kernel_uuid']+' v=1 '
HELPER='ASUS49-SYSCLOCK run='+I['helper_uuid']
CLOCK_PATH='kernel-syscall:syscall(SYS_clock_gettime);vDSO-bypassed;control='+I['control_uuid']+';loop=pure-compute-normal-final-only'
ENTRY=next(l.split('"')[1].replace('\\n','') for l in (R/'source/arch/arm64/kernel/asus_entry_tag.h').read_text().splitlines() if l.startswith('#define ASUS_ENTRY_TAG '))
BOUND=re.compile(re.escape(PREFIX)+r'(WENT|WRET) seq=([1-9][0-9]{0,2}) len=(0|[1-9][0-9]{0,3})(?: rc=(-?(?:0|[1-9][0-9]{0,3})))?')
EVENT=re.compile(r' phase=(\w+) stage=([\w.-]+) op=([\w.:-]+) path=(\S+) rc=(-?\d+) errno=(\d+) value=(.*)')
ALARM=' stage=alarm op=SIGALRM.fired nominal_seconds=1 timer_dependent=1'
ADMITTED=re.findall(r'PREFIX\("([^"\n]+)"\)',(R/'source/arch/arm64/kernel/asus_retained_trace.c').read_text())
LIMIT='WRET observes the point before original C return, not userspace resumption. A later PID1 WENT adds sequential boundary evidence; the alarm handler is a different user flow and may run between main-flow writes. Missing/torn/gapped/unknown records remain UNKNOWN. No absence proves CPU hang, allocation fault, reporting failure or execution loss. No storage advance or automatic fix.'
def decode(text,installed_full_sha256=None,fresh_boot_reference=None,complete_console_reference=None):
 p=json.loads((R/'evidence/packaging-receipt.json').read_text())
 bound=installed_full_sha256==p['full_p10']['sha256'] and bool(fresh_boot_reference and fresh_boot_reference.strip() and complete_console_reference and complete_console_reference.strip())
 result=dict(status='UNKNOWN_STOP',integrity='UNKNOWN',physical_binding=dict(exact_full_p10=installed_full_sha256==p['full_p10']['sha256'],fresh_stock_boot_reference=fresh_boot_reference,complete_console_reference=complete_console_reference,parent_attestations_only=True),calibration=dict(initial_clock_begin='UNKNOWN',initial_clock='UNKNOWN',normal_policy='UNKNOWN',frozen_control='UNKNOWN'),observed_boundaries=[],signal_handler_writes=[],limit=LIMIT)
 pairs=[];active=None;nextseq=1;errors=[];mode=False;alarm_count=0;budget_records=[];skip_records=[]
 result['pwrap_backstop']=dict(status='NOT_OBSERVED_UNKNOWN',records=budget_records,limit='Only captured samples; iterations are not elapsed time. Missing or undrained record cannot exclude poll/counter/read/delay nonprogress. Exhaustion plus later sustained normal progress supports this intervention, not hardware cause.')
 result['battery_uevent_omission']=dict(status='NOT_OBSERVED_UNKNOWN',records=skip_records,limit='Only a record correlated to the armed worker call establishes omission plus kobject return. Missing/stale/refused/undrained remains UNKNOWN; other AUXADC readers are preserved.')
 def fail(s):
  if s not in errors:errors.append(s)
 if installed_full_sha256 is not None and installed_full_sha256!=p['full_p10']['sha256']:fail('wrong installed full-p10 binding')
 if not text.endswith('\n'):fail('truncated final line')
 if any((ord(c)<32 and c!='\n') or ord(c)>126 for c in text):fail('torn/non-ASCII-control console')
 lines=text.splitlines()
 if not lines or lines[0]!=ENTRY:fail('fresh exact entry must be first console line')
 if text.count('ASUS49-ENTRY run=')!=1 or text.count('ASUS49-MODE run=')!=1:fail('missing/duplicate/mixed entry or mode')
 for pos,line in enumerate(lines):
  if line.startswith('ASUS49-MODE'):
   if line!=I['mode'] or active is not None:fail('wrong mode/order')
   mode=line==I['mode'];continue
  if 'ASUS49-BUEV' in line:
   m=SKIP.fullmatch(line)
   if not m or not mode or skip_records:
    fail('unknown/stale/malformed/duplicate battery omission record');continue
   first,before,after,rc=map(int,m.groups())
   if not 0<=before<first<=after<=2**32-1 or not -(2**31)<=rc<=2**31-1:
    fail('battery omission count/correlation/return range mismatch');continue
   skip_records.append(dict(line=pos,first_scoped_omission=first,before_call=before,after_return=after,omissions_in_interval=after-before,same_task=True,actual_kobject_call_returned=True,kobject_uevent_rc=rc,battery_property_getters_omitted=True))
   result['battery_uevent_omission']['status']='OMISSION_AND_KOBJECT_RETURN_CAPTURED'
   continue
  if 'ASUS49-PWRAP' in line:
   m=BUDGET.fullmatch(line)
   if not m or not mode or budget_records:
    fail('unknown/stale/malformed/duplicate pwrap budget record');continue
   start,last,wait,ready,rc=map(int,m.groups())
   if max(start,last)>2**64-1 or rc!=(0 if ready else -110):
    fail('pwrap field range/result mismatch');continue
   budget_records.append(dict(line=pos,start_ns=start,last_existing_clock_ns=last,iterations=16777216,wait_id=wait,wait_name={0:'other/unknown',1:'idle',2:'WFVLDCLR'}[wait],final_ready=bool(ready),returned_result=rc,captured_sample_delta_ns=last-start,last_sample_below_original_start=last<start,wall_time_from_iterations=False))
   result['pwrap_backstop']['status']='EXHAUSTION_RECORD_CAPTURED'
   continue
  if 'ASUS49-KMSG' in line:
   m=BOUND.fullmatch(line)
   if not m or not mode:
    fail('unknown/stale/malformed/overflow boundary marker');continue
   kind,seq,length,rc=m.groups();seq=int(seq);length=int(length)
   if not 1<=seq<=768 or not 0<=length<=992:fail('sequence/length outside source admission');continue
   if kind=='WENT':
    if rc is not None or active is not None or seq!=nextseq:fail('entry duplicate/gap/order');continue
    active=dict(seq=seq,length=length,entry_line=pos,logs=[]);pairs.append(active);nextseq+=1
   else:
    if rc is None or active is None or (seq,length)!=(active['seq'],active['length']):fail('return without matching entry/length/order');continue
    rc=int(rc)
    if m[4]=='-0':fail('noncanonical return rc')
    if rc not in (length,-12,-14):fail('unexpected original return rc')
    if rc<0 and active['logs']:fail('early error with captured LOG')
    active.update(return_line=pos,rc=rc);active=None
   continue
  if 'ASUS49-SYSCLOCK' in line:
   if not line.startswith(HELPER):fail('stale/malformed helper identity');continue
   tail=line[len(HELPER):];m=EVENT.fullmatch(tail);signal=tail==ALARM
   if not signal and (not m or not any(tail.startswith(s) for s in ADMITTED)):
    fail('malformed/unadmitted helper LOG');continue
   if active is None:fail('LOG without open WENT');continue
   # Frozen helper writes <6> + this ASCII line + newline. log_store strips
   # priority/newline. No second user copy was added to the instrument.
   if len(line.encode('ascii',errors='replace'))+4!=active['length']:fail('LOG/input length mismatch')
   if active['logs']:fail('multiple LOGs in a write; interleaving cannot be assigned');continue
   e=dict(line=pos,text=line,signal_handler=signal)
   if m:
    phase,stage,op,path,rc,err,value=m.groups();e.update(phase=phase,stage=stage,op=op,path=path,rc=int(rc),errno=int(err),value=value)
   active['logs'].append(e)
   if signal:alarm_count+=1;result['signal_handler_writes'].append(dict(seq=active['seq'],line=pos,main_flow_inference=False))
   continue
  if 'ASUS49-WDT run=' in line and not line.startswith('ASUS49-WDT run='+I['kernel_uuid']+' '):fail('stale watchdog identity')
  if re.search(r'A49(?:CAP1|SW2|WD1|PS1|PM1|DL1) uuid=',line):fail('hot observer unexpectedly enabled')
  if line.startswith('A49'):fail('unknown/hot marker')
  if 'ASUS49-' in line and not (line==ENTRY or line.startswith('ASUS49-WDT run='+I['kernel_uuid']+' ')):fail('unknown instrument marker')
 if alarm_count>1:fail('duplicate one-shot alarm LOG')
 # Calibration and observed boundaries are separate. A partial tail is evidence
 # of captured points only; it never turns an absence into a causal verdict.
 events=[]
 for j,w in enumerate(pairs):
  log=w['logs'][0] if w['logs'] else None;ret='return_line' in w
  fact=dict(seq=w['seq'],input_length=w['length'],WENT=True,LOG=bool(log),WRET=ret,rc=w.get('rc'),later_PID1_write_entry=pairs[j+1]['seq'] if j+1<len(pairs) else None,signal_handler=('OBSERVED_ALARM_HANDLER' if log['signal_handler'] else 'MAIN_FLOW_LOG') if log else 'UNKNOWN',span='WRET_REACHED_BEFORE_C_RETURN' if ret else ('LOG_CAPTURED_WRET_UNKNOWN' if log else 'WENT_CAPTURED_LOG_WRET_UNKNOWN'))
  if log:
   fact['helper_LOG']=log['text'];events.append((w,log))
  result['observed_boundaries'].append(fact)
 def rows(op,stage=None,path=None):return [(w,e) for w,e in events if e.get('op')==op and (stage is None or e.get('stage')==stage) and (path is None or e.get('path')==path)]
 def calibrated(rows,predicate):
  return len(rows)==1 and len(rows[0][0]['logs'])==1 and rows[0][0].get('rc')==rows[0][0]['length'] and predicate(rows[0][1])
 cp=rows('clock.path','actual','CLOCK_MONOTONIC');initial_begin=rows('clock_gettime','begin','loop.initial');initial=rows('clock_gettime','end','loop.initial');normal=rows('sched.original','actual','pid0')
 if calibrated(cp,lambda e:e['rc']==e['errno']==0 and e['value']==CLOCK_PATH):result['calibration']['frozen_control']='TRIPLE_OBSERVED_REUSED_HELPER_CONTROL'
 elif cp:fail('stale/invalid frozen control or missing control WRET')
 if calibrated(initial_begin,lambda e:e['rc']==e['errno']==0 and e['value']=='-'):result['calibration']['initial_clock_begin']='TRIPLE_OBSERVED'
 if calibrated(initial,lambda e:e['rc']==e['errno']==0 and bool(re.fullmatch(r'\d+\.\d{9}',e['value']))):result['calibration']['initial_clock']='TRIPLE_OBSERVED'
 if calibrated(normal,lambda e:e['rc']==e['errno']==0 and e['value']=='getparam_rc=0 getparam_errno=0 priority=0'):result['calibration']['normal_policy']='TRIPLE_OBSERVED_POLICY0_PRIORITY0'
 if cp and initial_begin and initial and normal and not cp[0][0]['seq']<initial_begin[0][0]['seq']<initial[0][0]['seq']<normal[0][0]['seq']:fail('control/initial/policy order mismatch')
 completion=rows('runnable.loop','complete','CLOCK_MONOTONIC')
 if completion and (len(completion)!=1 or completion[0][1]['rc']!=0 or completion[0][1]['errno']!=0 or completion[0][1]['value']!='control='+I['control_uuid']+' iterations=2000000 checksum=e4ca7075 reason=compute-cap'):fail('stale/malformed final completion')
 if rows('runnable.progress') or rows('clock_gettime.final') or any(e.get('op','').startswith(('sched.boost','sched.restore')) for _,e in events):fail('prior helper variant facts')
 if active:fail('incomplete final write; missing boundary UNKNOWN')
 # Execution observations are separate from omission and from C/syscall return.
 def facts(predicate):
  return [dict(seq=w['seq'],phase=e.get('phase'),stage=e.get('stage'),op=e.get('op'),path=e.get('path'),rc=e.get('rc'),errno=e.get('errno'),value=e.get('value'),WRET_before_C_return='return_line' in w) for w,e in events if predicate(e)]
 result['execution_facts']=dict(compute_completion=facts(lambda e:e.get('op')=='runnable.loop'),afterIRQ=facts(lambda e:e.get('phase')=='after' and e.get('op','').startswith('interrupts.')),alarm_handler_count=alarm_count,finish=facts(lambda e:e.get('phase')=='finish'),limit='Fast 2M completion is not 30-second stability. Alarm can remain unfired before normal finish. WRET remains pre-C-return; absence exonerates neither execution nor reporting. Positive skip plus compute/afterIRQ supports workload dependence, not a unique mechanism; a negative with skip weakens this trigger only.')
 result['errors']=errors
 if errors:
  result['battery_uevent_omission']['status']='INVALID_CONSOLE_UNKNOWN'
 if not errors:result['integrity']='OBSERVED_RECORD_ORDER_VALID_NO_VISIBLE_GAP'
 allcal=all(v!='UNKNOWN' for v in result['calibration'].values())
 if not errors and allcal and bound:result['status']='CALIBRATED_BOUNDARY_FACTS_STOP'
 elif not errors:result['status']='BOUNDARY_FACTS_PENDING_CALIBRATION_OR_BINDING_STOP'
 return result
if __name__=='__main__':
 a=argparse.ArgumentParser(description=__doc__);a.add_argument('console',type=Path);a.add_argument('--installed-full-sha256');a.add_argument('--fresh-stock-boot-reference');a.add_argument('--complete-console-reference');v=a.parse_args()
 print(json.dumps(decode(v.console.read_text(errors='replace'),v.installed_full_sha256,v.fresh_stock_boot_reference,v.complete_console_reference),indent=2))
