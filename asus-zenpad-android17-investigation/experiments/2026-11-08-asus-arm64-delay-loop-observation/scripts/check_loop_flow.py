"""Small actual ARM64 CFG check: counter/relax/return event order per path."""
import re

def check(d,start_reg):
 ins={}
 for l in d.splitlines():
  m=re.match(r'^\s*([0-9a-f]+):\s+[0-9a-f]{8}\s+([a-z.]+)\s*(.*)',l)
  if m:ins[int(m[1],16)]=(m[2],m[3].split('//')[0].strip())
 assert ins
 events={}
 for a,(op,args) in ins.items():
  if op=='mrs' and 'cntvct_el0' in args:reg=args.split(',')[0]
  elif op=='blr':
   no,na=ins[a+4];assert no=='mov' and na.split(',')[1].strip()=='x0';reg=na.split(',')[0]
  elif op in ('yield','ret'):events[a]=op;continue
  else:continue
  events[a]='start' if reg==start_reg else 'condition'
 def edges(a):
  op,args=ins[a]
  if op=='ret':return []
  if op=='b':return [int(args.split()[0],16)]
  if op.startswith('b.') or op in ('cbz','cbnz','tbz','tbnz'):return [int(args.split(',')[-1].strip().split()[0],16),a+4]
  return [a+4]
 def frontier(todo):
  seen=set();out=set()
  while todo:
   a=todo.pop();assert a in ins,('outside __delay',hex(a))
   if a in events:out.add(events[a]);continue
   if a in seen:continue
   seen.add(a);todo.extend(edges(a))
  return out
 assert frontier([min(ins)])=={'start'}
 for a,event in events.items():
  f=frontier(edges(a))
  assert f=={'start':{'condition'},'condition':{'yield','ret'},'yield':{'condition'},'ret':set()}[event],(hex(a),event,f)
 return dict(status='PASS_ACTUAL_ARM64_COUNTER_RELAX_RETURN_CFG',static_counter_sites=sum(v in ('start','condition') for v in events.values()),initial_sites=sum(v=='start' for v in events.values()),condition_sites=sum(v=='condition' for v in events.values()),path_language='start condition (yield condition)* return; each counter site direct CNTVCT or selected stable accessor, no path adds a read',diagnostic_calls='treated as returning; their nonreturn remains an observation interval, not a loop timeout')
