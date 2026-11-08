"""Decode one complete parent-provided console locally; no target contact."""
from pathlib import Path
import argparse,json,re
import decode as legacy
UUID='8e5c5d4d-6f94-4569-bfc6-63d92bac94a4'
SIZE=3648;OFFSET=384;ROW=320;RING=8
FIELDS=['sequence','raw_cntvct','prev_pid','prev_state_bits','next_pid','next_prio','next_policy','prev_prio','preempt_count','context','capture_serial_anchor','current_func','current_work','worker_flags']
HFIELDS=['generation','total','first_retained','last_retained','wraps','retained_count','cpu','nr_cpu_ids']
LIMITS=['Observation begins only after cap_init publishes readiness; earlier switches are unobserved.',
 'Ring covers only first_retained..last_retained; fixed slots retain the latest observed PID1 out/in through total.',
 'A switch to PID1 establishes kernel task selection, not userspace execution.',
 'Finite snapshots cannot prove permanent starvation, a wedge, continued later IRQ delivery, or root cause.',
 'CNTVCT is a raw register sample, not a timekeeping call or a guarantee of counter stability.',
 'The serial anchor orders against existing capture entries on the admitted CPU; it is not a timestamp.',
 'current_func/current_work are own-worker snapshots only; pointers remain parent-private until offline symbolization.',
 'A NULL current_func means no active function at this seam; it does not exclude later work.',
 'An active function snapshot does not establish culprit, permanent starvation, or execution after finish_task_switch.',
 'Timing can be perturbed by synchronous encoding/cache cleaning under the existing rq lock.']
def guard(label,uuid):return ('A49SGUARD '+label+' '+uuid).ljust(63).encode()+b'\n'
def numbers(line,n):
 values=[]
 for i in range(n):
  v=line[9+i*17:25+i*17]
  assert re.fullmatch(b'[0-9a-f]{16}',v) and line[25+i*17:26+i*17]==b' ', 'noncanonical numeric field'
  values.append(int(v,16))
 return values

def decode(data,uuid=UUID):
 old=legacy.decode(data,uuid)
 result=dict(status='UNKNOWN',uuid=uuid,legacy_status=old['status'],limits=LIMITS,records=[])
 try:
  tag=('A49SW2 uuid='+uuid).encode();starts=[m.start() for m in re.finditer(re.escape(tag),data)]
  assert len(starts)==1,'switch identity absent or ambiguous'
  start=starts[0];a=data[start:start+SIZE]
  assert len(a)==SIZE,'truncated switch area'
  assert a[:64]==tag.ljust(63)+b'\n','identity line padding'
  oldtag=('A49CAP1 uuid='+uuid).encode();oldstarts=[m.start() for m in re.finditer(re.escape(oldtag),data)]
  assert len(oldstarts)==1 and start==oldstarts[0]+legacy.SIZE,'switch area not immediately after legacy 5952 bytes'
  assert a[320:384]==guard('BEGIN',uuid) and a[-64:]==guard('END  ',uuid),'guard corruption'
  loss=a[256:320]
  result['sticky_state']=loss.rstrip().decode('ascii',errors='replace')
  assert loss==b'A49SLOSS 0 guard=0 busy=0 admission=0 overflow=0'.ljust(63)+b'\n','sticky loss or malformed latch'
  h=a[64:256];v=numbers(h,8);meta=dict(zip(HFIELDS,v));result['bounds']=meta
  assert h[:9]==b'VA49SH   ' and h[160:176]==h[9:25] and h[-1:]==b'\n','torn metadata'
  p=bytearray(h);p[:9]=b' '*9
  for i in range(8):p[9+i*17:25+i*17]=b' '*16
  p[160:176]=b' '*16;p[-1]=32
  assert all(x==32 for x in p),'metadata padding'
  total=meta['total'];first=max(1,total-7) if total else 0
  assert total<=2**64-2,'overflowed total'
  assert meta['generation']==total+1 and meta['first_retained']==first and meta['last_retained']==total and meta['retained_count']==min(total,8) and meta['wraps']==((total-1)//8 if total else 0),'metadata bounds'
  assert meta['cpu']==0 and (not total or meta['nr_cpu_ids']==1),'CPU admission'
  records=[]
  for slot in range(10):
   line=a[OFFSET+slot*ROW:OFFSET+(slot+1)*ROW];f=numbers(line,14)
   assert line[:9]==('VA49S %02x '%slot).encode() and line[-1:]==b'\n' and line[288:304]==line[9:25], 'torn switch row '+str(slot)
   assert re.fullmatch(b'[0-9a-f]{32}',line[248:280]),'comm encoding'
   p=bytearray(line);p[:9]=b' '*9
   for i in range(14):p[9+i*17:25+i*17]=b' '*16
   p[248:280]=b' '*32;p[288:304]=b' '*16;p[-1]=32
   assert all(x==32 for x in p),'row padding'
   r=dict(zip(FIELDS,f));r.update(slot=slot,comm_hex=line[248:280].decode());seq=r['sequence']
   comm=bytes.fromhex(r['comm_hex']);r['next_comm']=comm.split(b'\0',1)[0].decode('ascii',errors='backslashreplace')
   if not seq:
    assert not any(f) and comm==bytes(16),'nonempty zero row'
   else:
    assert seq<=total and r['context']==1,'sequence/context admission'
    assert r['preempt_count']==2,'unexpected scheduler preempt count'
    assert r['worker_flags'] in (0,1,3),'invalid worker flags'
    assert r['worker_flags']==3 or (r['current_func']==0 and r['current_work']==0),'pointers without own-worker validity'
    for k in ['prev_pid','next_pid','next_prio','next_policy','prev_prio']:assert r[k]<=0xffffffff,'field width'
   r['PF_WQ_WORKER']=bool(r['worker_flags'] & 1)
   r['worker_present']=bool(r['worker_flags'] & 2)
   r['active_work_assessment']=('active_function_snapshot' if r['current_func'] else 'no_active_function_at_seam') if r['worker_present'] else ('worker_unavailable' if r['PF_WQ_WORKER'] else 'not_workqueue_worker')
   if slot<8:
    expected=total-((total-1-slot)%8) if total else 0
    expected=expected if expected>0 else 0
    assert seq==expected,'ring chronology inconsistent'
   elif seq:
    assert r['prev_pid' if slot==8 else 'next_pid']==1,'fixed PID1 slot identity'
   records.append(r)
  by={r['sequence']:r for r in records[:8] if r['sequence']}
  for fixed,key in [(records[8],'prev_pid'),(records[9],'next_pid')]:
   seq=fixed['sequence'];seen=[r['sequence'] for r in records[:8] if r['sequence'] and r[key]==1]
   assert not seen or seq==max(seen),'fixed slot not latest observed PID1 transition'
   if seq in by:assert {k:v for k,v in fixed.items() if k!='slot'}=={k:v for k,v in by[seq].items() if k!='slot'},'fixed/ring mismatch'
  chronological=sorted(by.values(),key=lambda r:r['sequence'])
  assert all(a['capture_serial_anchor']<=b['capture_serial_anchor'] for a,b in zip(chronological,chronological[1:])),'serial anchor horizon regressed'
  for fixed in records[8:]:
   if fixed['sequence'] and fixed['sequence']<first and chronological:
    assert fixed['capture_serial_anchor']<=chronological[0]['capture_serial_anchor'],'fixed anchor beyond retained horizon'
  result['records']=sorted([r for r in records[:8] if r['sequence']],key=lambda r:r['sequence'])
  result['last_PID1_out']=records[8] if records[8]['sequence'] else None
  result['last_PID1_in']=records[9] if records[9]['sequence'] else None
  assert old['status']=='COMPLETE_CAPTURE_ROWS','legacy capture not admitted'
  result['status']='FINITE_SWITCH_CAPTURE' if total else 'UNKNOWN'
  if not total:result['reason']='ready area contains no observed switches'
 except (AssertionError,ValueError,IndexError) as exc:
  result['reason']=str(exc)
 return result
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('console',type=Path);p.add_argument('--uuid',default=UUID);a=p.parse_args()
 print(json.dumps(decode(a.console.read_bytes(),a.uuid),indent=2))
