"""Scoped CFG check: each original primitive sits between its own pre/post hooks."""
from pathlib import Path
import re,json
R=Path(__file__).resolve().parents[1];s=(R/'evidence/scoped-hooks.disasm').read_text()
funcs={}
for m in re.finditer(r'^([0-9a-f]+) <([^>]+)>:\n',s,re.M):
 end=re.search(r'\n\n',s[m.end():]);text=s[m.end():m.end()+end.start()] if end else s[m.end():];rows={}
 for l in text.splitlines():
  q=re.match(r'^([0-9a-f]+):\s+[0-9a-f]+\s+([.\w]+)\s*(.*)',l)
  if q:rows[int(q[1],16)]=(q[2],q[3])
 funcs[m[2]]=rows
checks={}
for name,brackets in {
 'asus_p00a_pmic_present':{4:('pmic_read_interface',5)},
 'asus_p00a_pmic_adc':{26:('__pm_stay_awake',27),28:('mutex_lock',29),30:('p00a_pmic_prepare_adc',31),32:('pmic_config_interface',33),34:('pmic_config_interface',35),36:('pmic_config_interface',37),38:('__const_udelay',39),40:('pmic_read_interface',41),44:('usleep_range',45),48:('mutex_unlock',49),50:('__pm_relax',51)},
 'p00a_pmic_prepare_adc':{61:('_raw_spin_lock_irqsave',62),63:('regmap_read',64),65:('regmap_read',66),67:('pmic_config_interface_nolock',68),69:('_raw_spin_unlock_irqrestore',70),74:('usleep_range',75)}
}.items():
 rows=funcs[name];addresses=sorted(rows);events={}
 for a,(op,args) in rows.items():
  if op=='bl':
   target=re.search(r'<([^>]+)>',args)[1]
   if target.startswith('asus_capture_pmic_'):
    reg='w1' if target.endswith('step') else 'w2'
    prev=[rows[x] for x in addresses if a-48<=x<a]
    value=next((int(m[1],16) for op,args in reversed(prev) if op=='mov' and (m:=re.match(reg+r', #0x([0-9a-f]+)',args))),None)
    assert value is not None,(name,hex(a),reg)
    events[a]=('S' if reg=='w1' else 'B',value)
   else:events[a]=('P',target)
 def edges(a):
  op,args=rows[a]
  if op=='ret':return []
  if op=='b':return [int(args.split()[0],16)]
  if op.startswith('b.') or op in ['cbz','cbnz','tbz','tbnz']:
   target=int(re.search(r'\b([0-9a-f]+) <',args)[1],16);return [a+4,target]
  return [a+4]
 def next_events(a,skip_printk=False):
  todo=edges(a);seen=set();found=set()
  while todo:
   b=todo.pop()
   if b in seen:continue
   seen.add(b);assert b in rows,(name,hex(a),hex(b))
   if b in events:
    if skip_printk and events[b]==('P','printk'):todo.extend(edges(b));continue
    found.add(b)
   else:todo.extend(edges(b))
  return found
 result={}
 for pre,(target,post) in brackets.items():
  starts=[a for a,e in events.items() if e==('S',pre)];assert starts,(name,pre)
  counts=0
  for a in starts:
   prim=next_events(a);assert prim and all(events[b]==('P',target) for b in prim),(name,pre,[events[b] for b in prim])
   for b in prim:
    after=next_events(b,skip_printk=True);assert after and all(events[z]==('S',post) for z in after),(name,pre,target,[events[z] for z in after]);counts+=1
  result[str(pre)]=dict(original_primitive=target,post_code=post,linked_pre_sites=len(starts),each_path_has_exactly_one_original_call_before_post=True,compiler_error_unlock_duplication_allowed_per_source_branch=counts>1)
 checks[name]=result
assert 'p00a_pmic_prepare_adc' in funcs
out=dict(status='PASS_SCOPED_LINKED_CALL_ORDER',functions=checks,scope='Only three changed driver function CFGs; BL sites and branch traversal until next observable call; inherited error-only printk inside inline original nolock read may intervene before its POST',ABI='exported present(int*) and adc(unsigned,int,int*) source declarations unchanged; AArch64 callers retain x0/x1/x2, linked status captured as w4 from preserved original ret and w0 restored in epilogue; prepare alone gets instrumentation parent pointer',return_review='All original source return expressions and p00a_pmic_result transform unchanged; actual return/status neighborhoods saved in linked-seams; host original-vs-candidate single scenario agrees',no_new_lock_spans_primitive='Every PRE/POST is a completed call. Publication unlock precedes hook return; CFG brackets contain the original call and its original scalar argument/result handling only. Source/ELF recorder allowlist excludes PMIC/driver/sleep/allocator/timekeeper calls.')
(R/'evidence/hook-abi.json').write_text(json.dumps(out,indent=2)+'\n');print(out['status'])
