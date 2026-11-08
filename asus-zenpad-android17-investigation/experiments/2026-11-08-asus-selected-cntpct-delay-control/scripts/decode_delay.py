"""Strict finite delay decoder. Its numeric-pointer output stays parent-private."""
from pathlib import Path
import argparse,json,re
import decode_pmic as pmic
import decode_power as power
ROOT=Path(__file__).resolve().parents[1];UUID=json.loads((Path(__file__).resolve().parents[1]/'evidence/identity.json').read_text())['run_uuid']
BASE=26752;SIZE=2560;U64=(1<<64)-1
FIELDS=['generation','stage','iteration','counter','cycles','preempt','context','pid']
LIMITS=['Finite retained interval only; missing start/return is UNKNOWN boundary, not automatic trap/stall or source cause.',
 'Only selected delay values are physical. Subtract only the selected physical start, never old PMIC/IRQ virtual values.',
 'Completed selected physical read proves current access only; success supports route hypothesis with timing confound, not global health/production fix.',
 'Milestones count original condition reads, not elapsed wall time; zero first delta can be normal at13MHz.',
 'Sparse preempt and actual IRQ-mask contexts do not establish IRQ arrival history or masking between samples.',
 'Effective cycles and observed LPJ operands are calibration facts, not proof of corruption.',
 'Loss/refusal/no arm/wrong route/torn/ambiguous join is UNKNOWN STOP; parent consults Large before further guesses.']
def canonical(line,tag,count,size=192,tail=160):
 assert len(line)==size and line[:9]==('V'+tag[1:]).encode() and line[-1:]==b'\n','marker/width'
 assert line[tail:tail+16]==line[9:25],'generation tail'
 f=[];blank=bytearray(line);blank[:9]=b' '*9;blank[-1]=32
 for j in range(count):
  v=line[9+j*17:25+j*17];assert re.fullmatch(b'[0-9a-f]{16}',v),'hex'
  f.append(int(v,16));blank[9+j*17:25+j*17]=b' '*16
 blank[tail:tail+16]=b' '*16;assert all(v==32 for v in blank),'noncanonical padding'
 return f

def area(data,uuid):
 starts=[m.start() for m in re.finditer(re.escape(('A49DL2 uuid='+uuid).encode()),data)];assert len(starts)==1,'delay identity absent/ambiguous'
 old=[m.start() for m in re.finditer(re.escape(('A49CAP1 uuid='+uuid).encode()),data)];assert len(old)==1,'old identity absent/ambiguous'
 start=starts[0];assert start==old[0]+BASE,'append adjacency';a=data[start:start+SIZE];assert len(a)==SIZE,'append truncated'
 assert a[:64]==('A49DL2 uuid='+uuid).ljust(63).encode()+b'\n','identity padding'
 assert a[256:320]==b'A49DLOSS 0 guard=0 busy=0 admission=0 overflow=0'.ljust(63)+b'\n','sticky loss/refusal'
 for off,label in [(320,'BEGIN'),(SIZE-64,'END  ')]:assert a[off:off+64]==('A49DGUARD '+label+' '+uuid).ljust(63).encode()+b'\n','guard'
 h=canonical(a[64:256],'!A49DH   ',9,tail=168);gen,state,seq,pid,hook,const,caller,mask,domain=h
 assert 0<gen<=U64 and 1<=state<=5 and seq and pid<=pmic.U32 and mask<128,'no arm/state/width'
 assert domain==(1 if state>=3 else 0),'selected read_domain/backend'
 j=canonical(a[384:960],'!A49DJ   ',30,576,552);assert j[29]==gen and j[0]==seq,'join generation'
 join=dict(zip(pmic.FIELDS,j[:29]));assert join['code']==38 and join['channel']==6 and join['samples']==5 and join['sample']<5 and not join['parent_token'],'exact PMIC target'
 assert join['pid']==pid and 0<join['token']==join['entry_seq']<=seq,'PMIC local identity'
 assert join['context']&4 and join['context']&10==10 and not join['context']&48,'PMIC task context'
 calc=canonical(a[960:1152],'!A49DC   ',8)
 if state==1:assert not any(calc) and not const and not caller and not mask,'armed state'
 else:
  cg,xloops,lpj,hz,product,cycles,cc,site=calc
  assert cg==gen and cc==const and xloops==1288500 and hz==250,'calculation identity'
  assert product==(xloops*lpj*hz)&U64 and cycles==product>>32,'single original unsigned arithmetic'
 rows=[]
 for slot in range(7):
  f=canonical(a[1152+slot*192:1344+slot*192],'!A49DS   ',8)
  if not mask&(1<<slot):assert not any(f),'unadvertised/stale slot';continue
  r=dict(zip(FIELDS,f));assert r['generation']==gen and r['stage']==slot and r['pid']==pid,'stage identity'
  assert r['cycles']==calc[5] and r['preempt']<=pmic.U32 and r['context'] in (4,5),'actual stage context'
  if slot==0:assert r['iteration']==r['counter']==0,'before marker'
  elif slot==1:assert r['iteration']==0,'start marker'
  elif slot<6:assert r['iteration']=={2:1,3:256,4:65536,5:1048576}[slot],'milestone count'
  else:assert 1<=r['iteration']<U64,'return iteration saturation/loss'
  rows.append(r)
 prefix=mask&63;assert prefix in (0,1,3,7,15,31,63),'milestone order'
 if state in (1,2):assert mask==0 and not caller,'pre-loop state'
 if state==3:assert not mask&64 and caller,'active loop state'
 if state in (4,5):assert mask&64 and mask&7==7 and caller,'return state'
 if mask&2:
  start=next(r['counter'] for r in rows if r['stage']==1)
  ret=rows[-1] if mask&64 else None
  for r in rows:
   if 2<=r['stage']<6 and r['iteration']<(ret['iteration'] if ret else max(x['iteration'] for x in rows)):
    assert ((r['counter']-start)&U64)<r['cycles'],'nonterminal unsigned condition'
 if mask&64:
  ret=rows[-1];start=next(r['counter'] for r in rows if r['stage']==1)
  assert ((ret['counter']-start)&U64)>=ret['cycles'],'return unsigned condition'
  for r in rows:
   if 2<=r['stage']<6:
    assert r['iteration']<=ret['iteration'],'milestone beyond return'
    if r['iteration']==ret['iteration']:assert r['counter']==ret['counter'],'original terminal value reused'
    else:assert ((r['counter']-start)&U64)<ret['cycles'],'continued after true termination'
 return dict(header=dict(generation=gen,state=state,pmic_sequence=seq,pid=pid,hook_caller=hook,const_caller=const,delay_caller=caller,stage_mask=mask,selected_read_domain=domain),join=join,calculation=dict(zip(['generation','xloops','lpj','HZ','product','cycles','caller','site'],calc)),milestones=rows)

def decode(data,uuid=UUID):
 out=dict(status='UNKNOWN',outcome='UNKNOWN_STOP',uuid=uuid,target=dict(status='UNKNOWN'),limits=LIMITS)
 try:
  old=pmic.decode(data,uuid);out['previous_statuses']=dict(pmic=old['status'],**old.get('previous_statuses',{}));out['old_target_facts']=old.get('target')
  assert old['status']=='FINITE_PMIC_CAPTURE' and old['target']['status']=='JOINED_FINITE_PMIC_STAGE','five protocols/exact target not admitted'
  d=area(data,uuid);out.update(d);h=d['header'];j=d['join'];calc=d['calculation'];lt=json.loads((ROOT/'evidence/linked-capture.json').read_text());routes=lt['delay_callers']
  readroute=lt['delay_read_routes'];assert readroute['status']=='PASS_ACTUAL_ELF_ROUTES' and readroute['uuid']==uuid and readroute['selected_read_domain']==1 and readroute['raw_physical_bypasses_virtual_OOL'],'compiled selected physical route proof'
  assert readroute['vmlinux_sha256']==json.loads((ROOT/'evidence/build-receipt.json').read_text())['artifacts']['vmlinux']['sha256'],'route ELF identity'
  assert len(readroute['selected_condition_sites'])==2 and readroute['selected_start_site'],'selected raw read-site pins'
  assert h['hook_caller']==routes['pre_return'] and j['caller'] in lt['pmic_callers']['voltage_adc_returns'],'compiled source route'
  if h['state']>=2:assert h['const_caller']==calc['caller']==routes['const_return'] and calc['site']==routes['calc_site'],'compiled calculation route'
  if h['state']>=3:assert h['delay_caller']==routes['delay_return'],'compiled actual spin caller'
  # Old strict decoder already verifies fresh work/body/property/name/callback,
  # time/anchor horizons and caller source. Join immutable PRE against that
  # exact current ADC identity, never against a historical PID/sample constant.
  adc=old['snapshots'].get('adc');assert adc,'no current ADC snapshot'
  stable=['pid','parent_token','channel','samples','token','property_token','property_seq','property_raw','body_token','body_phase','work','psy','callback','property_enum','entry_raw','entry_seq','caller']
  assert all(j[k]==adc[k] for k in stable),'immutable PMIC/property/body/work identity mismatch'
  assert j['sequence']<=adc['sequence'] and j['entry_raw']<=j['raw_cntvct']<=adc['raw_cntvct'],'PRE horizon'
  for k in ['capture_anchor','switch_anchor','work_anchor','power_anchor']:assert j[k]<=adc[k],'PRE anchor horizon'
  for r in old['records']+list(old['snapshots'].values()):
   if r['sequence']==j['sequence']:assert all(j[k]==r[k] for k in pmic.FIELDS),'copied PRE differs'
   if r['sequence']>j['sequence'] and r['token']==j['token'] and r['code']==38:raise AssertionError('later target arm missing')
  if adc['code']==38:assert all(j[k]==adc[k] for k in pmic.FIELDS),'earlier completed sample cannot masquerade as current PRE'
  if h['state']==5:assert adc['sequence']>j['sequence'],'post state horizon'
  # If matching code39 is retained, it must agree with the final state.
  matchingpost=[r for r in old['records']+list(old['snapshots'].values()) if r['token']==j['token'] and r['code']==39 and r['sample']==j['sample']]
  if matchingpost:assert h['state']==5,'retained POST disagrees with generation'
  out['outcome']='UNKNOWN_STOP' if h['state']<4 else 'SELECTED_RETURN_OBSERVED_ADC_POST_SEPARATE' if h['state']==4 else 'SELECTED_RETURN_AND_MATCHED_ADC_POST_OBSERVED_PID1_SEPARATE';out['status']='FINITE_DELAY_CAPTURE';out['target']=dict(status='JOINED_FINITE_DELAY',pid=j['pid'],pmic_token=j['token'],property_token=j['property_token'],body_token=j['body_token'],sample=j['sample'],generation=h['generation'],state={1:'ARMED_BEFORE_CALCULATION',2:'CALCULATED_BEFORE_DELAY_BEGIN',3:'DELAY_ACTIVE_FINITE',4:'RETURN_MARKER_BEFORE_POST',5:'MATCHED_PMIC_POST'}[h['state']],stages=[r['stage'] for r in d['milestones']],selected_read_domain=h['selected_read_domain'],current_physical_access_observed=bool(h['stage_mask']&2),requested_cycles=calc['cycles'] if h['state']>=2 else None,interpretation='FINITE_BOUNDARY_ONLY')
 except (AssertionError,ValueError,KeyError,IndexError,TypeError,OSError) as e:out['reason']=str(e) or type(e).__name__;out['target']=dict(status='UNKNOWN',reason=out['reason'])
 return out
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('console',type=Path);p.add_argument('--uuid',default=UUID);a=p.parse_args();print(json.dumps(decode(a.console.read_bytes(),a.uuid),indent=2))
