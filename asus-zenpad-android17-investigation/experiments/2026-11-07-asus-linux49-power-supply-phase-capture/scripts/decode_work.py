"""Strict offline decode of a complete parent console. Numeric addresses stay local."""
from pathlib import Path
import argparse,json,re
import decode as legacy
import decode_switch as scheduler
UUID='b4702f9a-6b32-423f-b789-d2bd515c0707'
SIZE=5568;OFFSET=384;ROW=320;RING=16;COMBINED=15168
FIELDS=['sequence','token','kind','raw_cntvct','pid','function','work','preempt_count_before','context','capture_serial_anchor','switch_total_anchor','ready','PF_WQ_WORKER','nr_cpu_ids']
HFIELDS=['generation','total','first_retained','last_retained','wraps','retained_count','entries','nr_cpu_ids']
LIMITS=[
 'Only admitted observations after readiness are covered; token-zero calls and early work are outside this horizon.',
 'Entry is immediately before the original indirect call. It bounds dispatch-to-postcall, including hook return, dispatch and instrumentation overhead; it does not prove function-body entry.',
 'A missing postcall in a finite snapshot does not prove permanent hang, duration, root cause or future nonreturn.',
 'Return tokens may outlive their entry ring slots; missing entries outside the 16-event horizon are explicitly UNKNOWN.',
 'A latest entry is attributed to the latest selected worker only after PID/comm/worker/context and scheduler-anchor cross-joins.',
 'CNTVCT is a single raw register sample, not a clock API or a proof of counter stability.',
 'Numeric function/work identities are captured before the call; returns carry only a local token and zero pointer fields.',
 'No lock or IRQ mask introduced by this recorder is held across the actual work function. Normal spin-unlock preemption may occur before hook return; encoding/cache cleaning can perturb timing.',
 'UNKNOWN stops interpretation; no automatic retry, next build, physical GO or fullOS GO.'
]
def guard(label,uuid):return ('A49WGUARD '+label+' '+uuid).ljust(63).encode()+b'\n'
def canonical(line,prefix,n,tail,comm=False):
 assert line[:9]==prefix and line[-1:]==b'\n' and line[tail:tail+16]==line[9:25], 'invalid marker or torn generation'
 f=scheduler.numbers(line,n);p=bytearray(line);p[:9]=b' '*9
 for i in range(n):p[9+i*17:25+i*17]=b' '*16
 p[tail:tail+16]=b' '*16;p[-1]=32
 if comm:
  assert re.fullmatch(b'[0-9a-f]{32}',line[248:280]),'invalid comm encoding'
  p[248:280]=b' '*32
 assert all(c==32 for c in p),'noncanonical padding'
 return f

def decode(data,uuid=UUID):
 result=dict(status='UNKNOWN',uuid=uuid,records=[],pairs=[],target=dict(status='UNKNOWN'),limits=LIMITS)
 try:
  old=legacy.decode(data,uuid);sw=scheduler.decode(data,uuid)
  result['legacy_status']=old['status'];result['scheduler_status']=sw['status']
  assert old['status']=='COMPLETE_CAPTURE_ROWS' and sw['status']=='FINITE_SWITCH_CAPTURE','legacy/scheduler capture not admitted'
  tag=('A49WD1 uuid='+uuid).encode();starts=[m.start() for m in re.finditer(re.escape(tag),data)]
  assert len(starts)==1,'work identity absent or ambiguous'
  start=starts[0];a=data[start:start+SIZE]
  assert len(a)==SIZE and a[:64]==tag.ljust(63)+b'\n','truncated/noncanonical identity'
  oldstart=data.index(('A49CAP1 uuid='+uuid).encode());assert start==oldstart+9600 and len(data)>=oldstart+COMBINED,'combined adjacency/range'
  oldtag=('A49CAP1 uuid='+uuid+' rows=15 row=384 fields=17 header=192').encode()
  assert data[oldstart:oldstart+128]==oldtag.ljust(127)+b'\n' and data[oldstart+128:oldstart+192]==b'A49FAULT 0'.ljust(63)+b'\n','legacy header padding/identity'
  assert a[320:384]==guard('BEGIN',uuid) and a[-64:]==guard('END  ',uuid),'work guard corruption'
  loss=a[256:320];result['sticky_state']=loss.rstrip().decode('ascii',errors='replace')
  assert loss==b'A49WLOSS 0 guard=0 busy=0 admission=0 overflow=0'.ljust(63)+b'\n','sticky work loss or malformed latch'
  h=a[64:256];m=dict(zip(HFIELDS,canonical(h,b'VA49WH   ',8,160)));result['bounds']=m
  total=m['total'];first=max(1,total-15) if total else 0
  assert total<=2**64-2 and m['generation']==total+1,'overflow/torn metadata'
  assert m['first_retained']==first and m['last_retained']==total and m['retained_count']==min(total,16) and m['wraps']==((total-1)//16 if total else 0),'finite horizon metadata'
  assert m['entries']<=total and m['nr_cpu_ids']==1,'entry count/CPU admission'
  records=[]
  capmax=max([0]+[r[k]>>8 for r in old['records'] for k in ['enter','exit','parent']])
  for slot in range(16):
   line=a[OFFSET+slot*ROW:OFFSET+(slot+1)*ROW]
   f=canonical(line,('VA49W %02x '%slot).encode(),14,288,True);r=dict(zip(FIELDS,f));r['slot']=slot;r['comm_hex']=line[248:280].decode();comm=bytes.fromhex(r['comm_hex']);r['comm']=comm.split(b'\0',1)[0].decode('ascii',errors='backslashreplace')
   seq=r['sequence'];expected=total-((total-1-slot)%16) if total else 0;expected=max(0,expected)
   assert seq==expected,'ring chronology inconsistent'
   if not seq:
    assert not any(f) and comm==bytes(16),'nonempty zero row'
    continue
   assert r['kind'] in (1,2) and 0<r['token']<=m['entries'],'kind/pair token'
   assert 0<r['pid']<=0xffffffff and r['preempt_count_before']<=0xffffffff,'PID/preempt width'
   assert r['context'] in (14,15) and r['ready']==1 and r['nr_cpu_ids']==1 and r['PF_WQ_WORKER'] in (0,1),'readiness/context admission'
   assert r['capture_serial_anchor']<=capmax and r['switch_total_anchor']<=sw['bounds']['total'],'anchor beyond capture horizon'
   if r['kind']==1:assert r['function'] and r['work'],'entry missing numeric identity'
   else:assert not r['function'] and not r['work'],'postcall carries pointer fields'
   records.append(r)
  records.sort(key=lambda r:r['sequence']);result['records']=records
  for x,y in zip(records,records[1:]):
   assert all(x[k]<=y[k] for k in ['raw_cntvct','capture_serial_anchor','switch_total_anchor']),'event ordering anchor regressed'
  entries=[r for r in records if r['kind']==1];returns=[r for r in records if r['kind']==2]
  assert all(y['token']==x['token']+1 for x,y in zip(entries,entries[1:])),'entry identities not consecutive'
  if entries:assert entries[-1]['token']==m['entries'],'latest entry identity mismatch'
  if total<=16:assert len(entries)==m['entries'],'unwrapped entry count mismatch'
  by={r['token']:r for r in entries};returned={}
  for r in returns:
   token=r['token'];assert token not in returned,'duplicate postcall token';returned[token]=r
   if token in by:
    e=by[token];assert e['sequence']<r['sequence'] and e['pid']==r['pid'],'pair order/PID mismatch'
   else:assert first>1 and (not entries or token<entries[0]['token']),'missing entry inside horizon'
  for e in entries:
   ret=returned.get(e['token']);result['pairs'].append(dict(token=e['token'],pid=e['pid'],entry_sequence=e['sequence'],return_sequence=ret['sequence'] if ret else None,status='PAIRED_POSTCALL' if ret else 'NO_POSTCALL_IN_FINITE_CAPTURE'))
  for r in returns:
   if r['token'] not in by:result['pairs'].append(dict(token=r['token'],pid=r['pid'],entry_sequence=None,return_sequence=r['sequence'],status='UNKNOWN_ENTRY_OUTSIDE_RING_HORIZON'))
  swrows={r['sequence']:r for r in sw['records']+[sw['last_PID1_out'],sw['last_PID1_in']] if r}
  for r in records:
   anchor=r['switch_total_anchor']
   for seq,s in swrows.items():
    if seq<=anchor:assert s['raw_cntvct']<=r['raw_cntvct'] and s['capture_serial_anchor']<=r['capture_serial_anchor'],'prior switch/work ordering mismatch'
    else:assert s['raw_cntvct']>=r['raw_cntvct'] and s['capture_serial_anchor']>=r['capture_serial_anchor'],'later switch/work ordering mismatch'
   if anchor in swrows:assert r['pid']==swrows[anchor]['next_pid'],'work PID differs from contemporaneous selected task'
  latest=swrows[sw['bounds']['total']];target=dict(status='UNKNOWN',selected_sequence=latest['sequence'],selected_pid=latest['next_pid'],selected_comm=latest['next_comm']);result['target']=target
  if entries:
   e=entries[-1];target['latest_entry_sequence']=e['sequence']
   joined=(e['switch_total_anchor']==latest['sequence'] and e['pid']==latest['next_pid'] and e['comm_hex']==latest['comm_hex'] and latest['worker_flags']==3 and e['PF_WQ_WORKER']==1 and e['context']==14 and e['preempt_count_before']==0)
   if joined:
    ret=returned.get(e['token']);target.update(status='SELECTED_WORKER_POSTCALL_RECORDED' if ret else 'SELECTED_WORKER_DISPATCH_BOUNDARY_NO_POSTCALL_IN_FINITE_CAPTURE',token=e['token'],function=e['function'],work=e['work'],return_sequence=ret['sequence'] if ret else None)
   else:target['reason']='latest entry does not join latest selected worker with normal task context'
  else:target['reason']='no entry retained; early or overwritten entry is UNKNOWN'
  result['status']='FINITE_WORK_CAPTURE' if total else 'UNKNOWN'
  if not total:result['reason']='ready area contains no work events'
 except (AssertionError,ValueError,IndexError,KeyError) as exc:result['reason']=str(exc)
 return result
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('console',type=Path);p.add_argument('--uuid',default=UUID);a=p.parse_args();print(json.dumps(decode(a.console.read_bytes(),a.uuid),indent=2))
