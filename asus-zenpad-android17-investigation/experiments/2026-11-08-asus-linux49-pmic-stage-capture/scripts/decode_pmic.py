"""Finite PMIC stages. Numeric identities are parent-private; missing post is an interval only."""
from pathlib import Path
import argparse,json,re,hashlib,gzip
import decode_power as power
import decode_work as work
import decode_switch as scheduler
import decode as clock
ROOT=Path(__file__).resolve().parents[1]
UUID=json.loads((ROOT/'evidence/identity.json').read_text())['run_uuid']
BASE=20544;SIZE=6208;ROW=576;OFFSET=384;RING=6;ROWS=10
U64=(1<<64)-1;U32=(1<<32)-1;NONE=0x80000000
FIELDS=['sequence','token','code','raw_cntvct','pid','parent_token','channel','samples','sample','poll','status','preempt','context','capture_anchor','switch_anchor','work_anchor','power_anchor','property_token','property_seq','property_raw','body_token','body_phase','work','psy','callback','property_enum','entry_raw','entry_seq','caller']
CODES={1:'PRESENT_ENTRY',2:'PRESENT_READINESS_PRE',3:'PRESENT_READY',4:'PRESENT_READ_PRE',5:'PRESENT_READ_POST',6:'PRESENT_DETECTOR_UNSUPPORTED',7:'PRESENT_NOT_READY',9:'PRESENT_RETURN',20:'ADC_ENTRY',21:'ADC_ARGUMENTS_VALID',22:'ADC_ARGUMENTS_REJECTED',23:'ADC_READINESS_PRE',24:'ADC_READY',25:'ADC_NOT_READY',26:'AWAKE_PRE',27:'AWAKE_POST',28:'MUTEX_LOCK_PRE',29:'MUTEX_LOCK_POST',30:'PREPARE_CALL_PRE',31:'PREPARE_CALL_POST',32:'VBUF_CONFIG_PRE',33:'VBUF_CONFIG_POST',34:'TRIGGER0_CONFIG_PRE',35:'TRIGGER0_CONFIG_POST',36:'TRIGGER1_CONFIG_PRE',37:'TRIGGER1_CONFIG_POST',38:'UDELAY300_PRE',39:'UDELAY300_POST',40:'POLL_READ_PRE',41:'POLL_READ_POST',42:'POLL_READY_BRANCH',43:'POLL_WAIT_BRANCH',44:'POLL_SLEEP_PRE',45:'POLL_SLEEP_POST',46:'POLL_TIMEOUT_BRANCH',47:'SAMPLE_COMPLETED',48:'OUT_MUTEX_UNLOCK_PRE',49:'OUT_MUTEX_UNLOCK_POST',50:'RELAX_PRE',51:'RELAX_POST',59:'ADC_RETURN',60:'PREPARE_ENTRY',61:'PREPARE_SPIN_LOCK_PRE',62:'PREPARE_SPIN_LOCK_POST',63:'PREPARE_DELAY_READ_NOLOCK_PRE',64:'PREPARE_DELAY_READ_NOLOCK_POST',65:'PREPARE_BUSY_READ_NOLOCK_PRE',66:'PREPARE_BUSY_READ_NOLOCK_POST',67:'PREPARE_CONFIG_NOLOCK_PRE',68:'PREPARE_CONFIG_NOLOCK_POST',69:'PREPARE_SPIN_UNLOCK_PRE',70:'PREPARE_SPIN_UNLOCK_POST',71:'PREPARE_ERROR_BRANCH',72:'PREPARE_READY_BRANCH',73:'PREPARE_WAIT_BRANCH',74:'PREPARE_SLEEP_PRE',75:'PREPARE_SLEEP_POST',76:'PREPARE_TIMEOUT_BRANCH',79:'PREPARE_RETURN'}
NEXT={1:{2},2:{3,7},3:{4},4:{5},5:{6,9},6:{9},7:{9},9:set(),20:{21,22},21:{23},22:{59},23:{24,25},24:{26},25:{59},26:{27},27:{28},28:{29},29:{30},30:{31},31:{32,48},32:{33},33:{34,48},34:{35},35:{36,48},36:{37},37:{38,48},38:{39},39:{40},40:{41},41:{42,43,48},42:{47},43:{44},44:{45},45:{40,46},46:{48},47:{34,48},48:{49},49:{50},50:{51},51:{59},59:set(),60:{61},61:{62},62:{63},63:{64},64:{65,69},65:{66},66:{67,69},67:{68},68:{69},69:{70},70:{71,72,73},71:{79},72:{79},73:{74},74:{75},75:{61,76},76:{79},79:set()}
INTERVALS={4:'existing pmic_read_interface(CHR_CON7) dispatch through post publication',26:'existing __pm_stay_awake dispatch through post publication',28:'existing mutex_lock(pmic_adc_mutex) dispatch through post publication',30:'existing prepare call through return publication; use joined prepare substage if retained',32:'existing VBUF pmic_config_interface dispatch through post publication',34:'existing trigger0 pmic_config_interface dispatch through post publication',36:'existing trigger1 pmic_config_interface dispatch through post publication',38:'existing udelay(300) dispatch through post publication',40:'existing poll pmic_read_interface dispatch through post publication',44:'existing poll usleep_range dispatch through post publication',48:'existing mutex_unlock dispatch, normal unlock preemption and post publication',50:'existing __pm_relax dispatch through post publication',61:'existing spin_lock_irqsave(pmic_adc_lock) dispatch through post publication',63:'existing prepare delay pmic_read_interface_nolock dispatch through post publication',65:'existing prepare busy pmic_read_interface_nolock dispatch through post publication',67:'existing prepare pmic_config_interface_nolock dispatch through post publication',69:'existing spin_unlock_irqrestore, ordinary unlock preemption and post publication',74:'existing prepare usleep_range dispatch through post publication'}
LIMITS=['Finite captured boundary only. Missing post includes recorder return, ordinary preemption, original primitive and post-hook entry/publication; it proves neither permanent hang, deadlock nor source cause.','Existing spin unlock and mutex unlock may preempt before the POST hook; the gap includes that preemption. No new lock/IRQ mask spans an original primitive.','No raw PMIC/ADC/mV/property output is captured. Return status 0 from present does not report the detector output.','Snapshots overwrite finitely. An unrelated latest present/ADC/prepare is UNKNOWN for attribution; broad admitted old property facts remain facts.','Any loss/torn/malformed/ambiguous identity is UNKNOWN STOP. No automatic trial/rebuild; parent consults Large before further guesses.']
def canonical(line,prefix,n,tail):
 assert len(line) in (192,ROW) and line[:9]==prefix and line[-1:]==b'\n','invalid line marker/width'
 assert line[tail:tail+16]==line[9:25],'torn generation/tail'
 f=scheduler.numbers(line,n);p=bytearray(line);p[:9]=b' '*9
 for j in range(n):p[9+j*17:25+j*17]=b' '*16
 p[tail:tail+16]=b' '*16;p[-1]=32
 assert all(ch==32 for ch in p),'noncanonical padding'
 return f
def category(code):return 'present' if code<20 else ('adc' if code<60 else 'prepare')
def reachable(a,b):
 seen=set();todo=list(NEXT[a])
 while todo:
  c=todo.pop()
  if c==b:return True
  if c not in seen:seen.add(c);todo.extend(NEXT[c])
 return False

def decode(data,uuid=UUID):
 out=dict(status='UNKNOWN',uuid=uuid,records=[],snapshots={},pairs=[],target=dict(status='UNKNOWN'),limits=LIMITS)
 try:
  old=power.decode(data,uuid);wd=work.decode(data,uuid);sw=scheduler.decode(data,uuid);cl=clock.decode(data,uuid)
  out['previous_statuses']=dict(power=old['status'],work=wd['status'],switch=sw['status'],clock=cl['status']);out['old_target_facts']=old['target']
  assert old['status']=='FINITE_POWER_CAPTURE','old protocols not all admitted'
  tag=('A49PM1 uuid='+uuid).encode();starts=[m.start() for m in re.finditer(re.escape(tag),data)]
  assert len(starts)==1,'PMIC identity absent/ambiguous'
  start=starts[0];oldstart=data.index(('A49CAP1 uuid='+uuid).encode());a=data[start:start+SIZE]
  assert start==oldstart+BASE and len(a)==SIZE,'append adjacency/size'
  assert a[:64]==tag.ljust(63)+b'\n','noncanonical identity'
  for off,label in [(320,'BEGIN'),(SIZE-64,'END  ')]:assert a[off:off+64]==('A49MGUARD '+label+' '+uuid).ljust(63).encode()+b'\n','guard corruption'
  assert a[256:320]==b'A49MLOSS 0 guard=0 busy=0 admission=0 overflow=0'.ljust(63)+b'\n','sticky loss or malformed latch'
  h=canonical(a[64:256],b'VA49MH   ',8,160);gen,total,first,last,wraps,count,reserved,cpus=h
  out['bounds']=dict(generation=gen,total=total,first_retained=first,last_retained=last,wraps=wraps,retained_count=count,nr_cpu_ids=cpus)
  assert total<=U64-1 and gen==total+1 and first==(max(1,total-RING+1) if total else 0) and last==total and wraps==((total-1)//RING if total else 0) and count==min(RING,total) and reserved==0 and cpus==1,'metadata horizon/generation/CPU'
  capmax=max([0]+[r[k]>>8 for r in cl['records'] for k in ['enter','exit','parent']])
  bounds=dict(capture_anchor=capmax,switch_anchor=sw['bounds']['total'],work_anchor=wd['bounds']['total'],power_anchor=old['bounds']['total'])
  rows=[];snap={}
  for slot in range(ROWS):
   line=a[OFFSET+slot*ROW:OFFSET+(slot+1)*ROW];f=canonical(line,('VA49M %02x '%slot).encode(),len(FIELDS),552);r=dict(zip(FIELDS,f));r['slot']=slot;seq=r['sequence']
   if slot<RING:assert seq==(max(0,total-((total-1-slot)%RING)) if total else 0),'ring chronology'
   else:assert seq<=total,'snapshot beyond header'
   if not seq:assert not any(f),'nonempty zero row';continue
   code=r['code'];assert code in CODES and 0<r['token']==r['entry_seq']<=seq,'code/local token'
   assert 0<r['pid']<=U32 and r['preempt']<=U32 and all(r[k]<=U32 for k in ['channel','samples','sample','poll','status','property_enum']),'integer width'
   ctx=r['context'];assert ctx&10==10 and ctx&~63==0 and not(ctx&4 and ctx&48) and (ctx&4 or ctx&48),'actual context bits'
   assert r['entry_raw']<=r['raw_cntvct'] and all(r[k]<=v for k,v in bounds.items()),'time/anchor horizon'
   for key in ['work','psy','callback','caller']:
    assert not r[key] or r[key]>=0xffffff8000000000,'non-kernel identity'
   assert r['caller'] and r['caller']%4==0,'caller return site identity'
   assert not r['parent_token'] if code<60 else 0<r['parent_token']<r['token'],'prepare parent identity'
   if code in (1,20,60):assert seq==r['token'] and r['raw_cntvct']==r['entry_raw'] and r['sample']==r['poll']==U32,'entry fields'
   if r['property_token']:
    assert 0<r['property_token']==r['property_seq']<=r['power_anchor'] and r['property_raw']<=r['entry_raw'] and r['psy'] and r['callback'],'property identity'
   else:assert not any(r[k] for k in ['property_seq','property_raw','body_token','body_phase','work','psy','callback','property_enum']),'unattributed context not zero'
   if code<20:assert r['channel']==r['samples']==0 and r['sample']==r['poll']==U32,'present payload'
   if 20<code<59 and code not in (22,):assert 4<=r['channel']<=7 and 1<=r['samples']<=32,'ADC accepted arguments'
   if 34<=code<=47:assert r['sample']<r['samples'],'sample horizon'
   if 40<=code<=47:assert r['poll']<100 or code==46 and r['poll']==100,'poll horizon'
   if code>=60:assert r['sample']==U32 and (r['poll']<=100 or code==60 and r['poll']==U32),'prepare poll horizon'
   r['stage']=CODES[code]
   if slot<RING:rows.append(r)
   else:
    name=['latest','present','adc','prepare'][slot-RING]
    assert name=='latest' or name==category(code),'snapshot category';snap[name]=r
  rows.sort(key=lambda r:r['sequence']);out.update(records=rows,snapshots=snap)
  allrows={}
  for r in rows+list(snap.values()):
   seq=r['sequence'];v={k:x for k,x in r.items() if k!='slot'}
   if seq in allrows:assert v=={k:x for k,x in allrows[seq].items() if k!='slot'},'snapshot/ring disagreement'
   else:allrows[seq]=r
  ordered=sorted(allrows.values(),key=lambda r:r['sequence'])
  assert not total or snap.get('latest',{}).get('sequence')==total,'missing/stale latest stage'
  for cat in ['present','adc','prepare']:
   seen=[r for r in rows if category(r['code'])==cat]
   if seen:assert snap.get(cat,{}).get('sequence',0)>=seen[-1]['sequence'],'category snapshot stale'
  for x,y in zip(ordered,ordered[1:]):assert all(x[k]<=y[k] for k in ['raw_cntvct',*bounds]),'chronology regressed'
  groups={}
  stable=['pid','parent_token','channel','samples','property_token','property_seq','property_raw','body_token','body_phase','work','psy','callback','property_enum','entry_raw','entry_seq','caller']
  for r in ordered:groups.setdefault(r['token'],[]).append(r)
  for token,rs in groups.items():
   x=rs[0];cat=category(x['code']);entrycode={'present':1,'adc':20,'prepare':60}[cat];endcode={'present':9,'adc':59,'prepare':79}[cat]
   assert all(category(r['code'])==cat and all(r[k]==x[k] for k in stable) for r in rs),'local pair identity changed'
   for x,y in zip(rs,rs[1:]):
    # All intervening events inside the ring are retained, even from other pairs.
    if x['sequence']>=first:assert y['code'] in NEXT[x['code']],'local stage skipped/reversed inside horizon'
    else:assert reachable(x['code'],y['code']),'local stage path reversed'
    if category(x['code'])=='prepare':assert y['poll']>=x['poll'] or x['code']==60,'prepare poll regressed'
    if category(x['code'])=='adc' and 34<=x['code']<=47 and 34<=y['code']<=47:
     assert y['sample']>=x['sample'],'sample regressed'
     if y['sample']==x['sample'] and 40<=x['code']<=47 and 40<=y['code']<=47:assert y['poll']>=x['poll'],'poll regressed'
   entry=next((r for r in rs if r['code']==entrycode),None);end=next((r for r in rs if r['code']==endcode),None)
   if not entry:assert token<first,'missing local entry inside retained horizon'
   out['pairs'].append(dict(token=token,parent_token=rs[0]['parent_token'],category=cat,pid=rs[0]['pid'],entry_retained=bool(entry),returned=bool(end),latest_stage=rs[-1]['stage'],status='RETURN_CHECKPOINT' if end else ('FINITE_PENDING_STAGE' if entry else 'ENTRY_OUTSIDE_RING_HORIZON')))
  # Cross-protocol anchors are actual fresh counts, never historical constants.
  swrows={r['sequence']:r for r in sw['records']+[sw['last_PID1_out'],sw['last_PID1_in']] if r}
  psrows={r['sequence']:r for r in old['records']+list(old['snapshots'].values())}
  for r in ordered:
   if r['switch_anchor'] in swrows:assert r['pid']==swrows[r['switch_anchor']]['next_pid'],'selected task/PID mismatch'
   for older,key in [(list(swrows.values()),'switch_anchor'),(wd['records'],'work_anchor'),(list(psrows.values()),'power_anchor')]:
    for v in older:
     if v['sequence']<=r[key]:assert v['raw_cntvct']<=r['raw_cntvct'],'earlier anchor time mismatch'
     else:assert v['raw_cntvct']>=r['raw_cntvct'],'later anchor time mismatch'
  out['status']='FINITE_PMIC_CAPTURE' if total else 'UNKNOWN'
  t=old['target'];p=old['snapshots'].get('property');b=old['snapshots'].get('body');lt=json.loads((ROOT/'evidence/linked-capture.json').read_text())
  if t.get('status')!='JOINED_LAST_BODY_CHECKPOINT' or t.get('property',{}).get('status')!='JOINED_LOCAL_PAIR':
   out['target']=dict(status='UNKNOWN',reason='old target join ambiguous');return out
  if not(p and b and p['property']=='POWER_SUPPLY_PROP_batt_vol' and p['name']=='battery' and p['psy']==b['psy'] and p['callback']==int(lt['symbols']['battery_get_property']['address'],16)):
   out['target']=dict(status='UNKNOWN',reason='target is not exact named battery voltage callback');return out
  def joined(r):
   return bool(r['context']&4 and r['pid']==p['pid'] and r['property_token']==p['token'] and r['property_seq']==p['entry_seq'] and r['property_raw']==p['entry_raw'] and r['body_token']==b['token'] and r['body_phase']==p['body_code'] and r['work']==p['work'] and r['psy']==p['psy'] and r['callback']==p['callback'] and r['property_enum']==p['detail'] and r['entry_raw']>=p['entry_raw'] and (p['code']==40 or r['raw_cntvct']<=p['raw_cntvct']) and r['power_anchor']>=p['entry_seq'] and r['work_anchor']>=p['work_anchor'] and r['switch_anchor']>=p['switch_anchor'] and r['capture_anchor']>=p['capture_anchor'])
  candidates=[];attribution={}
  adc=snap.get('adc')
  for cat in ['present','adc','prepare']:
   r=snap.get(cat);ok=bool(r and joined(r))
   if ok and cat=='present':ok=r['caller'] in lt['pmic_callers']['present_returns']
   if ok and cat=='adc':ok=r['channel']==6 and r['samples']==5 and r['caller'] in lt['pmic_callers']['voltage_adc_returns']
   if ok and cat=='prepare':ok=bool(adc and joined(adc) and adc['token']==r['parent_token'] and adc['code']==30 and r['channel']==adc['channel'] and r['samples']==adc['samples'] and r['entry_raw']>=adc['entry_raw'] and r['caller'] in lt['pmic_callers']['prepare_returns'] and (not lt['pmic_callers']['prepare_inlined'] or r['caller']==adc['caller']))
   attribution[cat]=dict(status='JOINED_CALLER_LOCAL' if ok else 'UNKNOWN',token=r['token'] if r else None,stage=r['stage'] if r else None)
   if ok:candidates.append(r)
  out['snapshot_attribution']=attribution
  if not candidates:out['target']=dict(status='UNKNOWN',reason='no fixed PMIC snapshot strictly joins fresh target property and compiled caller');return out
  latest=max(candidates,key=lambda r:r['sequence'])
  # An unrelated latest category does not become evidence for this target.
  latest_global=snap.get('latest')
  if latest_global and latest_global['sequence']>latest['sequence'] :out['target']=dict(status='UNKNOWN',reason='later unrelated PMIC stage prevents target attribution');return out
  code=latest['code'];out['target']=dict(status='JOINED_FINITE_PMIC_STAGE',pid=latest['pid'],work_token=t['work_token'],body_token=b['token'],property_token=p['token'],property=p['property'],supply=p['name'],pmic_token=latest['token'],parent_token=latest['parent_token'],source_function={'present':'asus_p00a_pmic_present','adc':'asus_p00a_pmic_adc','prepare':'p00a_pmic_prepare_adc'}[category(code)],channel=latest['channel'] if code>=20 else None,samples=latest['samples'] if code>=20 else None,sample=None if latest['sample']==U32 else latest['sample'],poll=None if latest['poll']==U32 else latest['poll'],stage=latest['stage'],code=code,return_status=None if latest['status']==NONE else (latest['status']-(1<<32) if latest['status']&(1<<31) else latest['status']),interval=INTERVALS.get(code,'checkpoint through next source checkpoint / caller continuation; no primitive is uniquely named'),interpretation='FINITE_BOUNDARY_ONLY_PARENT_INTERPRETATION')
 except (AssertionError,ValueError,IndexError,KeyError,OSError) as exc:
  out['status']='UNKNOWN';out['target']=dict(status='UNKNOWN',reason=str(exc));out['reason']=str(exc)
 return out
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('console',type=Path);p.add_argument('--uuid',default=UUID);a=p.parse_args();print(json.dumps(decode(a.console.read_bytes(),a.uuid),indent=2))
