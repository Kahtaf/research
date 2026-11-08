"""Finite power capture decoder. Keep numeric addresses parent-private until symbolized."""
from pathlib import Path
import argparse,hashlib,json,re
import decode as legacy
import decode_switch as scheduler
import decode_work as work
ROOT=Path(__file__).resolve().parents[1]
UUID=json.loads((ROOT/'evidence/identity.json').read_text())['run_uuid']
SIZE=5376;ROW=448;OFFSET=384;RING=8;BASE=15168;COMBINED=20544
FIELDS=['sequence','token','code','raw_cntvct','pid','work','psy','callback','detail','preempt','context','capture_anchor','switch_anchor','work_anchor','body_token','entry_raw','entry_seq','body_code','peer_psy','result']
CODES={1:'BODY_ENTRY',2:'FIRST_LOCK_PRE',3:'FIRST_LOCK_ACQUIRED',4:'CHANGED_TRUE_CLEAR_UNLOCK_PRE',5:'FIRST_UNLOCK_POST',6:'CLASS_PRE',7:'CLASS_POST',8:'LEDS_PRE',9:'LEDS_POST',10:'NOTIFIER_PRE',11:'NOTIFIER_POST',12:'UEVENT_PRE',13:'UEVENT_POST',14:'FINAL_LOCK_PRE',15:'FINAL_LOCK_ACQUIRED',16:'FINAL_CHANGED_DECISION',17:'PM_RELAX_PRE',18:'PM_RELAX_POST',19:'FINAL_UNLOCK_PRE',20:'BODY_RETURN_CHECKPOINT',21:'CHANGED_FALSE_BRANCH',40:'PROPERTY_ENTER',41:'PROPERTY_RETURN',50:'EXTERNAL_ENTER',51:'EXTERNAL_RETURN'}
U64=(1<<64)-1
NEXT={1:{2},2:{3},3:{4,21},4:{5},5:{6},6:{7},7:{8},8:{9},9:{10},10:{11},11:{12},12:{13},13:{14},14:{15},15:{16},21:{16},16:{17,19},17:{18},18:{19},19:{20},20:set()}
LIMITS=['Finite last checkpoint only; missing return does not prove permanent hang or cause.','Precall includes recorder return, preemption, original dispatch and postcall recorder entry/publication. Body-return checkpoint precedes the actual C return and old WQ postcall.','Normal raw-spin unlock preemption and cache cleaning can perturb the observation. No new lock/IRQ mask spans original operation.','Snapshots preserve local pair identity but have a finite overwrite horizon; unmatched outside-horizon entries do not invalidate the whole record. Target attribution without a unique join is UNKNOWN.','Actual atomic/IRQoff/preempt context is recorded; nonzero alone is not a fault. Unsupported NMI/reentry/loss/torn/ambiguous target stops; no retry.','Property values and driver-private payload are never captured.']
def guard(label,u):return ('A49PGUARD '+label+' '+u).ljust(63).encode()+b'\n'
def canonical(line,prefix,n,tail,names=False):
 assert len(line) in (192,448) and line[:9]==prefix and line[-1:]==b'\n','invalid marker/length'
 assert line[tail:tail+16]==line[9:25],'torn generation'
 f=scheduler.numbers(line,n);p=bytearray(line);p[:9]=b' '*9
 for i in range(n):p[9+i*17:25+i*17]=b' '*16
 p[tail:tail+16]=b' '*16;p[-1]=32
 if names:
  for a in (352,384):
   assert re.fullmatch(b'[0-9a-f]{32}',line[a:a+32]),'invalid name encoding'
   p[a:a+32]=b' '*32
 assert all(c==32 for c in p),'noncanonical padding'
 return f

def decode(data,uuid=UUID):
 out=dict(status='UNKNOWN',uuid=uuid,records=[],snapshots={},pairs=[],target=dict(status='UNKNOWN'),limits=LIMITS)
 try:
  old=legacy.decode(data,uuid);sw=scheduler.decode(data,uuid);wd=work.decode(data,uuid)
  out['previous_statuses']={k:v['status'] for k,v in [('clock',old),('switch',sw),('work',wd)]}
  assert old['status']=='COMPLETE_CAPTURE_ROWS' and sw['status']=='FINITE_SWITCH_CAPTURE' and wd['status']=='FINITE_WORK_CAPTURE','old capture not admitted'
  tag=('A49PS1 uuid='+uuid).encode();starts=[m.start() for m in re.finditer(re.escape(tag),data)]
  assert len(starts)==1,'power identity absent/ambiguous'
  start=starts[0];a=data[start:start+SIZE];oldstart=data.index(('A49CAP1 uuid='+uuid).encode())
  assert start==oldstart+BASE and len(a)==SIZE and len(data)>=oldstart+COMBINED,'append adjacency/capacity'
  assert a[:64]==tag.ljust(63)+b'\n','noncanonical identity'
  assert a[320:384]==guard('BEGIN',uuid) and a[-64:]==guard('END  ',uuid),'guard corruption'
  loss=a[256:320];out['sticky_state']=loss.rstrip().decode('ascii',errors='replace')
  assert loss==b'A49PLOSS 0 guard=0 busy=0 admission=0 overflow=0'.ljust(63)+b'\n','sticky loss/malformed latch'
  h=canonical(a[64:256],b'VA49PH   ',8,160);gen,total,first,last,wraps,count,reserved,cpus=h
  out['bounds']=dict(generation=gen,total=total,first_retained=first,last_retained=last,wraps=wraps,retained_count=count,nr_cpu_ids=cpus)
  assert total<=U64-1 and gen==total+1 and first==(max(1,total-7) if total else 0) and last==total and wraps==((total-1)//8 if total else 0) and count==min(8,total) and reserved==0 and cpus==1,'metadata horizon/generation/CPU'
  config=(ROOT/'artifacts/resolved.config').read_bytes()
  enum=json.loads((ROOT/'evidence/property-enum.json').read_text())
  assert hashlib.sha256(config).hexdigest()==enum['config_sha256'],'enum configuration identity'
  assert hashlib.sha256((ROOT/'source/base/include/linux/power_supply.h').read_bytes()).hexdigest()==enum['source_sha256'],'enum source identity'
  props={int(k):v for k,v in enum['properties'].items()}
  capmax=max([0]+[r[k]>>8 for r in old['records'] for k in ['enter','exit','parent']])
  records=[];snapshots={}
  for slot in range(11):
   line=a[OFFSET+slot*ROW:OFFSET+(slot+1)*ROW]
   f=canonical(line,('VA49P %02x '%slot).encode(),20,424,True);r=dict(zip(FIELDS,f));r['slot']=slot
   for key,at in [('name',352),('peer_name',384)]:
    encoded=line[at:at+32].decode();v=bytes.fromhex(encoded);r[key+'_hex']=encoded
    if b'\0' in v:assert not any(v[v.index(0):]),'noncanonical zero-padded name'
    r[key]=v.split(b'\0',1)[0].decode('ascii',errors='backslashreplace');r[key+'_truncated']=b'\0' not in v
   seq=r['sequence']
   if slot<8:
    expected=max(0,total-((total-1-slot)%8)) if total else 0
    assert seq==expected,'ring chronology'
   else:assert seq<=total,'snapshot beyond metadata'
   if not seq:
    assert not any(f) and not int(r['name_hex']+r['peer_name_hex'],16),'nonempty zero row'
    continue
   assert r['code'] in CODES and 0<r['token']==r['entry_seq']<=seq,'code/token'
   r['phase']=CODES[r['code']]
   assert 0<r['pid']<=0xffffffff and r['preempt']<=0xffffffff,'PID/preempt width'
   ctx=r['context'];assert ctx&10==10 and ctx&~63==0 and not (ctx&4 and ctx&48) and (ctx&4 or ctx&48),'context bits'
   # Atomic/IRQoff callbacks are admitted, not rejected for preempt != 0.
   assert r['detail']<=0xffffffff and (r['result']==U64 or r['result']<=0xffffffff),'detail/return width'
   assert r['entry_raw']<=r['raw_cntvct'] and r['capture_anchor']<=capmax and r['switch_anchor']<=sw['bounds']['total'] and r['work_anchor']<=wd['bounds']['total'],'time/anchor beyond horizon'
   for p in ['psy','work','callback','peer_psy']:
    v=r[p];assert not v or v>=0xffffff8000000000,'non-kernel pointer'
    if p in ['work','psy','peer_psy']:assert not v or v%8==0,'unaligned object identity'
    if p=='callback':assert not v or v%4==0,'unaligned callback identity'
   assert r['psy'],'missing supply identity'
   code=r['code']
   if code<40:
    assert r['work'] and not r['callback'] and not r['peer_psy'] and r['peer_name_hex']=='00'*16 and r['body_token']==r['token'] and r['body_code']==1,'body identity'
    assert r['detail'] in (0,1) and (code in [1,3,15,16] or r['detail']==0),'body changed flag'
    assert (r['result']<=0xffffffff if code in (7,11,13) else r['result']==U64),'body return status'
   else:
    assert r['callback'] and (not r['body_token'] or (r['body_token']<r['token'] and r['body_code'] in NEXT)),'callback/parent identity'
    if r['body_token']:assert r['work'],'parent lacks work'
    else:assert r['body_code']==0 and r['work']==0,'UNKNOWN parent malformed'
    if code in (40,41):
     assert r['detail'] in props and not r['peer_psy'] and r['peer_name_hex']=='00'*16,'property enum/peer'
     r['property']=props[r['detail']]
    else:assert r['peer_psy'] and r['detail']==0,'external supplier'
    assert (r['result']<=0xffffffff if code==41 else r['result']==U64),'callback return status'
   if code in (1,40,50):assert seq==r['token'] and r['entry_raw']==r['raw_cntvct'],'entry identity'
   if slot>=8:
    assert (code<40 if slot==8 else code in ((40,41) if slot==9 else (50,51))),'snapshot category'
    snapshots[['body','property','external'][slot-8]]=r
   else:records.append(r)
  records.sort(key=lambda r:r['sequence']);out.update(records=records,snapshots=snapshots)
  # Fixed snapshots and ring duplicates must agree bytewise apart from row slot.
  allrows={}
  for r in records+list(snapshots.values()):
   seq=r['sequence'];c={k:v for k,v in r.items() if k!='slot'}
   if seq in allrows:assert c=={k:v for k,v in allrows[seq].items() if k!='slot'},'snapshot/ring disagreement'
   else:allrows[seq]=r
  ordered=sorted(allrows.values(),key=lambda r:r['sequence'])
  for x,y in zip(ordered,ordered[1:]):
   assert all(x[k]<=y[k] for k in ['raw_cntvct','capture_anchor','switch_anchor','work_anchor']),'chronology regressed'
  for name,codes in [('body',set(NEXT)),('property',{40,41}),('external',{50,51})]:
   visible=[r for r in records if r['code'] in codes]
   if visible:assert name in snapshots and snapshots[name]['sequence']>=visible[-1]['sequence'],'snapshot stale'
  # Per-token local identities survive nested/interleaved callbacks and wrap.
  groups={}
  for r in ordered:groups.setdefault(r['token'],[]).append(r)
  stable=['pid','work','psy','callback','body_token','entry_raw','entry_seq','body_code','peer_psy','name_hex','peer_name_hex']
  for token,rs in groups.items():
   firstrow=rs[0];body=firstrow['code']<40
   assert all(all(r[k]==firstrow[k] for k in stable) for r in rs),'local pair identity changed'
   if body:
    for x,y in zip(rs,rs[1:]):
     if y['sequence']==x['sequence']+1:assert y['code'] in NEXT[x['code']],'body phase order'
    # Check order through skipped interleaved records via graph reachability.
    for x,y in zip(rs,rs[1:]):
     seen=set();todo=list(NEXT[x['code']])
     while todo:
      v=todo.pop()
      if v not in seen:seen.add(v);todo.extend(NEXT[v])
     assert y['code'] in seen,'body phase path regressed'
   else:
    assert all(r['detail']==firstrow['detail'] for r in rs),'property identity changed'
    assert len(rs)<=2 and (len(rs)==1 or [r['code'] for r in rs] in ([40,41],[50,51])),'duplicate/reversed callback pair'
    entry=next((r for r in rs if r['code'] in (40,50)),None);ret=next((r for r in rs if r['code'] in (41,51)),None)
    if not entry:assert token<first,'missing entry inside retained ring'
    out['pairs'].append(dict(token=token,pid=firstrow['pid'],supply=firstrow['name'],body_token=firstrow['body_token'],entry_sequence=entry['sequence'] if entry else None,return_sequence=ret['sequence'] if ret else None,status='PAIRED_RETURN' if entry and ret else ('NO_RETURN_IN_FINITE_CAPTURE' if entry else 'UNKNOWN_ENTRY_OUTSIDE_HORIZON')))
  swrows={r['sequence']:r for r in sw['records']+[sw['last_PID1_out'],sw['last_PID1_in']] if r}
  for r in ordered:
   if r['switch_anchor'] in swrows:assert r['pid']==swrows[r['switch_anchor']]['next_pid'],'event PID/selected-task mismatch'
   for s in swrows.values():
    if s['sequence']<=r['switch_anchor']:assert s['raw_cntvct']<=r['raw_cntvct'],'earlier switch time mismatch'
    else:assert s['raw_cntvct']>=r['raw_cntvct'],'later switch time mismatch'
   for w in wd['records']:
    if w['sequence']<=r['work_anchor']:assert w['raw_cntvct']<=r['raw_cntvct'],'earlier work time mismatch'
    else:assert w['raw_cntvct']>=r['raw_cntvct'],'later work time mismatch'
  out['status']='FINITE_POWER_CAPTURE' if total else 'UNKNOWN'
  target=out['target'];wt=wd['target'];target['work_status']=wt['status']
  b=snapshots.get('body')
  if not b or 'token' not in wt:
   target['reason']='no latest body or no uniquely joined latest WQ target';return out
  we=next((r for r in wd['records'] if r['kind']==1 and r['token']==wt['token']),None)
  assert we is not None
  linked=json.loads((ROOT/'evidence/linked-capture.json').read_text())
  assert we['function']==int(linked['symbols']['power_supply_changed_work']['address'],16),'WQ target is not exact named work function'
  entry=allrows.get(b['entry_seq'])
  # entry raw is preserved in every body phase. A retained entry strengthens,
  # but is not required for the snapshot's caller-local dispatch join.
  same=(b['work']==we['work'] and b['pid']==we['pid'] and b['entry_raw']>=we['raw_cntvct'] and b['work_anchor']>=we['sequence'] and b['token']==b['body_token'])
  intervening=[w for w in wd['records'] if we['sequence']<w['sequence']<=b['work_anchor'] and w['pid']==b['pid']]
  # Same-task nested jobs make joining ambiguous; other task interleaving is okay.
  if not same or any(w['kind']==1 or w['token']==we['token'] for w in intervening):
   target['reason']='latest body cannot uniquely join latest WQ entry before a postcall';return out
  if entry:assert entry['code']==1 and entry['work_anchor']>=we['sequence'],'body entry/dispatch order'
  target.update(status='JOINED_LAST_BODY_CHECKPOINT',work_token=we['token'],body_token=b['token'],pid=b['pid'],supply=b['name'],phase=b['phase'],code=b['code'],body_entry_retained=bool(entry),body_return_checkpoint=b['code']==20,actual_WQ_postcall_recorded=wt.get('return_sequence') is not None)
  # WQ postcall must be after every body checkpoint if it exists.
  wr=next((r for r in wd['records'] if r['kind']==2 and r['token']==we['token']),None)
  if wr:assert b['code']==20 and b['work_anchor']<wr['sequence'] and b['raw_cntvct']<=wr['raw_cntvct'],'postcall/body ordering'
  for category in ['property','external']:
   p=snapshots.get(category);joined=bool(p and p['body_token']==b['token'] and p['pid']==b['pid'] and p['entry_raw']>=b['entry_raw'] and p['work']==b['work'] and p['body_code'] in (6,8,10,12,17) and p['entry_seq']>b['token'])
   # Require an actual same-supply identity or the exact class consumer pair.
   supplyjoin=bool(joined and (p['psy']==b['psy'] and p['name_hex']==b['name_hex']))
   if category=='external':supplyjoin=bool(joined and p['peer_psy']==b['psy'] and p['peer_name_hex']==b['name_hex'] and p['body_code']==6)
   if category=='property' and joined and not supplyjoin:
    ext=snapshots.get('external')
    supplyjoin=bool(ext and ext['body_token']==b['token'] and ext['pid']==p['pid'] and ext['psy']==p['psy'] and ext['name_hex']==p['name_hex'] and ext['peer_psy']==b['psy'] and ext['peer_name_hex']==b['name_hex'] and ext['entry_seq']<p['entry_seq'] and ext['entry_raw']<=p['entry_raw'] and (ext['code']==50 or ext['raw_cntvct']>=p['raw_cntvct']) and p['body_code']==6)
   if supplyjoin:
    assert p['entry_raw']>=b['entry_raw'] and p['work_anchor']>=we['sequence'],'callback before body/dispatch'
    if p['code'] in (40,50):
     assert b['code']==p['body_code'] and b['raw_cntvct']<=p['entry_raw'],'pending callback after body left its phase'
    pre=next((r for r in ordered if r['token']==b['token'] and r['code']==p['body_code']),None)
    post=next((r for r in ordered if r['token']==b['token'] and r['code']==p['body_code']+1),None)
    if pre:assert pre['sequence']<p['entry_seq'] and pre['raw_cntvct']<=p['entry_raw'],'callback before phase pre'
    if post:assert p['code'] in (41,51) and p['sequence']<post['sequence'] and p['raw_cntvct']<=post['raw_cntvct'],'callback after phase post'
   target[category]=dict(status='JOINED_LOCAL_PAIR' if supplyjoin else 'UNKNOWN',token=p['token'] if p else None,supply=p['name'] if p else None,code=p['code'] if p else None,property=p.get('property') if p else None,body_phase_at_entry=CODES.get(p['body_code']) if p else None,returned=bool(p and p['code'] in (41,51)),reason=None if supplyjoin else 'latest callback snapshot lacks exact PID/body/time/supply join')
  # Explicitly keep the broad body phase usable when generic snapshot is unrelated.
  target['interpretation']='Finite boundary only; parent interprets one physical trial and stops.'
 except (AssertionError,ValueError,IndexError,KeyError,OSError) as exc:
  out['status']='UNKNOWN';out['target']=dict(status='UNKNOWN',reason=str(exc));out['reason']=str(exc)
 return out
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('console',type=Path);p.add_argument('--uuid',default=UUID);a=p.parse_args();print(json.dumps(decode(a.console.read_bytes(),a.uuid),indent=2))
