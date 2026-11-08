#!/usr/bin/env python3
"""Fixed repaired STOCK-KERNEL trial. Default PLAN_ONLY; parent-review gated."""
from __future__ import annotations
import argparse,copy,datetime as dt,fcntl,json,os,secrets,sys,time
from pathlib import Path
sys.dont_write_bytecode=True
import fixed as F
import observer as O
from transport import HostIO,Transport
E=F.E

class Journal(E.Journal):
 def save(self):F.durable(self.directory/'state.json',self.state)
 def finish(self,outcome,**data):
  data['manual_recovery_permitted']=False
  if 'next_action' in data:data['next_action']='Stock-only parent controller assesses the typed result; never select a manual boot mode or retry an unknown operation.'
  return super().finish(outcome,**data)

class RunState:
 def __init__(self,path,run,action,mode):
  self.path=path;self.data=dict(schema_version=2,profile=F.PROFILE,run_id=run,action=action,mode=mode,
   outcome='preparing',device_contacted=False,entry_requests=0,diagnostic_pass=False,report_classification='not_observed',
   stock_returned=False,p10_restored=False,cleanup_verified=False,events=[])
  self.save()
 def save(self):F.durable(self.path/'state.json',self.data)
 def event(self,kind,**data):
  self.data['events'].append(dict(at=dt.datetime.now(dt.timezone.utc).isoformat(),kind=kind,**data));self.save()
 def finish(self,outcome,**data):self.data.update(outcome=outcome,**data);self.save();return self.data

def source_pins():
 paths=sorted((F.S/'source/service').glob('*.py'))+sorted((F.S/'tests/service').glob('*.py'))
 paths += [F.AUTH,F.S/'evidence/service/firmware-audit.json',F.S/'evidence/service/firmware-emulation.json',
  F.S/'evidence/service/oem-system-rc.json',F.S/'artifacts/stock-boot.sepolicy',
  F.S/'artifacts/service/boot-init',F.S/'artifacts/service/boot-sbin_adbd',
  F.W/'2026-11-06-asus-recovery-control-wifi/evidence/parent-diagnostic-verification.json',
  F.W/'2026-11-06-asus-recovery-control-wifi/evidence/deadline-source-preservation.json',
  F.ENGINE,E.HELPER,E.ROOT_BINARY,F.ACCEPTANCE]
 return {str(p.relative_to(F.W)):F.sha(F.read(p)) for p in paths}

def contract():
 return dict(schema_version=2,profile=F.PROFILE,target=E.TARGET,endpoint=F.ENDPOINT,
  candidate_sha256=F.IMAGE_SHA,candidate_bytes=8654848,full_partition_sha256=F.FULL_SHA,
  stock_partition_sha256=F.STOCK_SHA,wrapped_kernel_sha256=F.KERNEL_SHA,para_preimage_sha256=F.PARA_SHA,
  entry=['adb','-t','same-run-fresh-stock-USB-transport-id','reboot','recovery'],
  entry_scope='exact audited stock adbd -> volatile sys.powerctl=reboot,recovery -> stock init RESTART2 recovery',
  image_deadline_seconds=120,maximum_observation_seconds=420,
  physical_roundtrip_proved_for_service_entry=False,
  source_and_evidence_sha256=source_pins())

def template():
 return dict(contract=contract(),parent_review=dict(approved=False,reviewer='',reviewed_at_utc='',valid_until_utc='2026-11-06T23:03:00+00:00',
  allow_one_unattended_stock_trial=False,user_authorization_record_reviewed=False,
  source_binary_entry_return_models_reviewed=False,static_evidence_not_physical_readiness_understood=False,
  other_writers_and_ota_excluded=False,allow_existing_authenticated_tcp_reenable=False))

def review(path,expected_hash,now=None):
 F.require(path is not None and isinstance(expected_hash,str) and __import__('re').fullmatch('[0-9a-f]{64}',expected_hash),'Reviewed file and independent SHA256 required')
 raw=F.read(path,256*1024);F.require(F.sha(raw)==expected_hash,'Parent review hash mismatch')
 value=F.unique_json(raw);F.require(set(value)=={'contract','parent_review'},'Unexpected review fields')
 F.require(value['contract']==contract(),'Reviewed source/evidence/fixed scope changed')
 r=value['parent_review'];expected=set(template()['parent_review']);F.require(type(r) is dict and set(r)==expected,'Unexpected parent review schema')
 for k in ('approved','allow_one_unattended_stock_trial','user_authorization_record_reviewed','source_binary_entry_return_models_reviewed',
           'static_evidence_not_physical_readiness_understood','other_writers_and_ota_excluded','allow_existing_authenticated_tcp_reenable'):
  F.require(r[k] is True,'Parent technical attestation missing: '+k)
 F.require(type(r['reviewer']) is str and 0<len(r['reviewer'].strip())<=256,'Parent reviewer missing')
 now=now or dt.datetime.now(dt.timezone.utc)
 try:at=dt.datetime.fromisoformat(r['reviewed_at_utc']);until=dt.datetime.fromisoformat(r['valid_until_utc'])
 except (ValueError,TypeError) as exc:raise F.Refused('Review timestamps invalid') from exc
 start=dt.datetime(2026,11,6,17,3,tzinfo=dt.timezone.utc);end=start+dt.timedelta(hours=6)
 F.require(at.tzinfo is not None and until.tzinfo is not None and start<=at<=now<=until<=end and until-at<=dt.timedelta(hours=6),'Review is stale/future or outside inherited unattended window')
 proof=F.unique_json(F.read(F.S/'evidence/service/firmware-audit.json'))
 emulation=F.unique_json(F.read(F.S/'evidence/service/firmware-emulation.json'))
 F.require(proof['status']=='EXACT_BINARY_STATIC_QUALIFIED_PENDING_PARENT_REVIEW' and proof['device_contacted'] is False
  and emulation['status']=='PASS' and emulation['device_contacted'] is False,'Entry qualification missing')
 return value

def consume_review(digest,run):
 parent=F.S/'evidence/service/consumed-reviews';parent.mkdir(mode=0o700,exist_ok=True)
 F.require(not parent.is_symlink(),'Review-intent directory is a symlink')
 F.durable(parent/(digest+'.json'),dict(run_id=run,review_sha256=digest,scope='one trial; no retry from this review',
  claimed_at=dt.datetime.now(dt.timezone.utc).isoformat()),exclusive=True)

def phase_directory(root,name):
 p=root/name;p.mkdir(mode=0o700,exist_ok=False);return p

def transport(root,run,phase,action,boot_id,host):
 p=phase_directory(root,phase);j=Journal(p,action,'UNATTENDED_STOCK_ONLY')
 return Transport(p,j,action,run,phase,boot_id,host),j

def restore_once(root,run,stock,boot_id,host,state):
 F.require(not state.data.get('restore_started'),'Stock inverse was already dispatched or attempted; no retry')
 state.data['restore_started']=True;state.event('stock_inverse_intent')
 t,j=transport(root,run,'restore','restore',boot_id,host)
 result=E.execute('restore',stock,None,t,j)
 verified=result['outcome'] in ('restored_full_hash_verified','verified_already_restored') and result['restore_verified'] is True
 cleanup=verified and result.get('cleanup')=='verified'
 state.data.update(p10_restored=verified,cleanup_verified=cleanup,restore_result=copy.deepcopy(result));state.save()
 return verified and cleanup


def run_trial(root,run,stock,candidate,host,state,reviewed,recheck_review,observer_type=O.Observer):
 """No mutating retry. Reads during expected reboot are bounded observation only."""
 nonce=secrets.token_hex(16);obs=None;installed=False;install_started=False;entry_started=False
 proof=F.unique_json(F.read(F.S/'evidence/service/firmware-audit.json'));rcs=proof['root_rc']
 try:
  baseline=O.make_pin(host,run,nonce)
  state.data['initial_stock_pin']=baseline;state.event('initial_stock_health_and_USB_verified')
  t,j=transport(root,run,'preflight','install',baseline['stock_boot_id'],host)
  t.safety_snapshot(F.STOCK_SHA,rcs)
  state.event('preinstall_stock_para_cache_binary_rc_geometry_verified')
  recheck_review()
  t,j=transport(root,run,'install','install',baseline['stock_boot_id'],host)
  install_started=True;state.event('install_engine_started')
  result=E.execute('install',stock,candidate,t,j)
  installed=result['outcome']=='installed_full_hash_verified' and result.get('cleanup')=='verified'
  state.data['install_result']=copy.deepcopy(result);state.save()
  if not installed:
   return state.finish('install_not_ready_stop',p10_restored=result.get('restore_verified',False),
    error='No entry and no additional inverse: inherited writer already handled any known failure')
  state.event('install_verified',full_partition_sha256=F.FULL_SHA)
  t,j=transport(root,run,'entry-guard','install',baseline['stock_boot_id'],host)
  t.safety_snapshot(F.FULL_SHA,rcs)
  pin=O.make_pin(host,run,nonce)
  F.require(pin['stock_boot_id']==baseline['stock_boot_id'],'Stock rebooted unexpectedly during installation')
  F.durable(root/'fresh-entry-pin.json',pin,exclusive=True)
  obs=observer_type(host,pin,run,nonce,root/'observer');obs.start()
  recheck_review()
  O.validate_pin(pin,run,nonce,time.monotonic())
  # Durable intent precedes the only entry dispatch. Never infer reset from EOF.
  F.durable(root/'entry-intent.json',dict(run_id=run,reviewed=reviewed['contract'],pin=pin,
   observer_ready=True,entry=['adb','-t',pin['initial_transport_id'],'reboot','recovery'],
   candidate_full_sha256=F.FULL_SHA,at=dt.datetime.now(dt.timezone.utc).isoformat()),exclusive=True)
  obs.arm();entry_started=True
  state.data['entry_requests']=1;state.event('entry_intent_durable_one_dispatch')
  delivery=host.entry(pin);state.data['entry_delivery']=delivery;state.event('entry_delivery_result',**delivery)
  if delivery['delivery']=='explicit_service_failure':
   # Only the exact audited adbd failure text and a still-identical healthy boot
   # permit an immediate inverse. Any observed reset instead uses observation.
   row=O.usb_row(host.inventory(),pin)
   if row is not None and row['serial']==F.SERIAL:
    snapshot=host.stock_snapshot(row)
    if O.stock_ready(snapshot) and snapshot['boot_id']==pin['stock_boot_id']:
     obs.stop()
     F.require(not obs.state['diagnostic_seen'] and not obs.state['stock_returned'] and not obs.state['error'],
               'Entry failure conflicts with observation')
     state.event('explicit_entry_failure_same_stock_boot_verified')
     returned=dict(row=row,snapshot=snapshot)
     host.ensure_tcp(pin,returned)
     ok=restore_once(root,run,stock,snapshot['boot_id'],host,state)
     return state.finish('entry_failed_stock_inverse_verified' if ok else 'entry_failed_inverse_unverified_stop')
  observed=obs.wait();state.data['observation']=observed
  state.data.update(diagnostic_pass=observed['diagnostic_pass'],report_classification=observed['report_classification'],stock_returned=observed['stock_returned']);state.save()
  if not observed['stock_returned'] or observed.get('error'):
   return state.finish('bounded_observation_no_verified_return_stop',
      error=observed.get('error') or 'No actual new stock boot within observation window; timeout is not a reset proof')
  state.event('stock_return_verified',report_classification=observed['report_classification'])
  # The observer thread has ended; no report/health probes race temporary root.
  host.ensure_tcp(pin,observed['stock_return'])
  ok=restore_once(root,run,stock,observed['stock_return']['snapshot']['boot_id'],host,state)
  if not ok:return state.finish('stock_returned_restore_unverified_stop')
  passed=observed['diagnostic_pass'] and observed.get('return_timing_consistent_with_120s_deadline') is True
  return state.finish('diagnostic_pass_stock_return_and_p10_restore_verified' if passed else 'stock_return_and_restore_verified_diagnostic_incomplete',
   timer_firing_physically_proved=False,return_timing_consistent_with_120s_deadline=observed.get('return_timing_consistent_with_120s_deadline',False))
 except (E.UncertainTransport,O.Unavailable) as exc:
  if obs:obs.stop()
  return state.finish('transport_uncertain_no_retry',error=str(exc),partition_may_be_candidate=installed)
 except (E.Refused,E.OperationFailed,E.VerificationFailed,OSError,ValueError,TypeError) as exc:
  if obs:obs.stop()
  state.event('guard_or_operation_failure',error=str(exc),entry_started=entry_started)
  if installed and not entry_started:
   try:
    # No entry has been dispatched; one fixed inverse is safe only through all
    # inherited fresh stock/geometry/boot-ID/readback guards.
    ok=restore_once(root,run,stock,baseline['stock_boot_id'],host,state)
    return state.finish('preentry_refused_stock_inverse_verified' if ok else 'preentry_refused_inverse_unverified_stop',error=str(exc))
   except (E.Refused,E.OperationFailed,E.VerificationFailed,E.UncertainTransport,O.Unavailable,OSError) as inverse:
    return state.finish('preentry_refused_inverse_unverified_stop',error=str(exc),inverse_error=str(inverse))
  return state.finish('refused_before_write' if not install_started else 'entry_or_cleanup_unverified_stop',error=str(exc),
                      partition_may_be_modified=install_started)


def preflight(root,run,stock,host,state):
 pin=O.make_pin(host,run,secrets.token_hex(16));proof=F.unique_json(F.read(F.S/'evidence/service/firmware-audit.json'))
 t,j=transport(root,run,'preflight','install',pin['stock_boot_id'],host);t.safety_snapshot(F.STOCK_SHA,proof['root_rc'])
 return state.finish('preflight_readonly_pass',preflight_pin=pin,
  pin_reusable_for_entry=False,stock_p10_verified=True,device_contacted=True)


def new_run(action):
 parent=F.S/'evidence/service/runs';parent.mkdir(mode=0o700,parents=True,exist_ok=True)
 F.require(not parent.is_symlink(),'Run parent is a symlink')
 run=dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ-')+secrets.token_hex(8)
 root=parent/run;root.mkdir(mode=0o700,exist_ok=False);return root,run

def main(argv=None):
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('action',choices=('plan','preflight','trial'))
 p.add_argument('--execute',action='store_true')
 p.add_argument('--unattended-stock-only',action='store_true')
 p.add_argument('--exclusive-device-owner',action='store_true')
 p.add_argument('--review',type=Path)
 p.add_argument('--reviewed-sha256')
 a=p.parse_args(argv);os.umask(0o077);root,run=new_run(a.action)
 state=RunState(root,run,a.action,'EXECUTE_UNATTENDED_STOCK_ONLY' if a.execute else 'PLAN_ONLY')
 try:
  stock,candidate,inputs=F.fixed_inputs();state.data['local_inputs']=inputs;state.save()
  F.durable(root/'review-template.json',template(),exclusive=True)
  if not a.execute:
   state.finish('plan_only_validated',device_contacted=False,planned_action=a.action,
    execute_requires='Separate actual parent technical review, --unattended-stock-only and --exclusive-device-owner; never --supervised')
  else:
   F.require(a.action!='plan','Plan action cannot execute')
   F.require(a.unattended_stock_only and a.exclusive_device_owner,'Explicit truthful unattended stock scope and parent exclusive ownership required')
   reviewed=review(a.review,a.reviewed_sha256)
   # This is the same lock inode used by the physically exercised writer.
   with E.EXECUTE_LOCK.open('a') as lock:
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    if a.action=='trial':consume_review(a.reviewed_sha256,run)
    state.data['device_contacted']=True;state.event('parent_review_and_exclusive_lock_verified',review_sha256=a.reviewed_sha256)
    host=HostIO(root/'commands')
    if a.action=='preflight':preflight(root,run,stock,host,state)
    else:run_trial(root,run,stock,candidate,host,state,reviewed,lambda:review(a.review,a.reviewed_sha256))
 except (E.Refused,E.UncertainTransport,E.OperationFailed,E.VerificationFailed,O.Unavailable,OSError,ValueError,KeyError,TypeError) as exc:
  state.finish('refused_or_stopped',error=str(exc))
 result=state.data
 print(json.dumps({k:result[k] for k in ('outcome','device_contacted','entry_requests','diagnostic_pass','report_classification','stock_returned','p10_restored','cleanup_verified')}|{'evidence':str(root)},indent=2))
 if result['outcome'] in ('plan_only_validated','preflight_readonly_pass','diagnostic_pass_stock_return_and_p10_restore_verified'):return 0
 return 3 if result['outcome']=='stock_return_and_restore_verified_diagnostic_incomplete' else 2

if __name__=='__main__':raise SystemExit(main())
