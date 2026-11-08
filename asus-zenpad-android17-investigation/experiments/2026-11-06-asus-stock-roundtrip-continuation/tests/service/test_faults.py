#!/usr/bin/env python3
"""Offline behavioral qualification. All external execution/network is prohibited."""
from __future__ import annotations
import contextlib,copy,datetime as dt,fcntl,io,json,os,subprocess,sys,tarfile,tempfile,time,unittest
from dataclasses import dataclass,field
from pathlib import Path
from typing import Any
from unittest.mock import patch
S=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(S/'source/service'));sys.dont_write_bytecode=True
import controller as C
import observer as O
import transport as T
import fixed as F
E=F.E

def isolation(event,args):
 if event.startswith(('socket.','subprocess.','os.spawn','os.exec','os.posix_spawn')) or event=='os.system':
  raise RuntimeError('OFFLINE: forbidden '+event)
sys.addaudithook(isolation)
RUN='20261106T200000Z-0123456789abcdef'
OLD='11111111-1111-1111-1111-111111111111';NEW='22222222-2222-2222-2222-222222222222'
STOCK=b'S'*1024;CANDIDATE=b'C'*1024
RESULTS=[]

def row(diag=False,tid='1'):
 return dict(F.DIAG_ROW if diag else F.STOCK_ROW,usb='fixture:1',transport_id=tid)
def snapshot(boot=OLD):
 return dict(F.STOCK_PROPS,enforce='Enforcing',uid='2000',context='u:r:shell:s0',kernel=F.KERNEL_BANNER,boot_id=boot,flash_recovery='stopped')
def valid_report():
 sections={'/tmp/diagnostic.txt':F.MARKER,'/proc/version':F.KERNEL_BANNER,
 '/proc/cmdline':'androidboot.serialno='+F.SERIAL,'/sys/fs/selinux/enforce':'1',
 '/proc/self/attr/current':'u:r:recovery:s0','/proc/uptime':'12.3 4.5',
 '/proc/mounts':'rootfs / rootfs rw 0 0'}
 return ('REPORT_ENDPOINT uid=2000 context=u:r:shell:s0\n'+''.join('[ '+p+' ]\n'+v+'\n' for p,v in sections.items())+'END_DIAGNOSTIC\n').encode()

@dataclass
class Device:
 """Physical effects model, independent of controller decisions."""
 block:bytes=STOCK
 para:bytes=b'unchanged para fixture'
 cache:bytes=b'unchanged cache fixture'
 staged:dict[str,bytes]=field(default_factory=dict)
 writes:list[str]=field(default_factory=list)
 calls:list[str]=field(default_factory=list)
 fault:str|None=None
 fault_kind:str='uncertain'
 lost_at:int|None=None
 counts:dict[str,int]=field(default_factory=dict)
 def step(self,label:str)->None:
  self.calls.append(label);self.counts[label]=self.counts.get(label,0)+1
  key=label+'#'+str(self.counts[label])
  if self.fault not in (label,key):return
  self.fault=None
  if self.fault_kind=='uncertain':
   self.lost_at=len(self.calls);raise E.UncertainTransport('fixture loss '+key)
  if self.fault_kind=='refused':raise F.Refused('fixture guard '+key)
  raise E.OperationFailed('fixture completed operation failure '+key)

class MemoryTransport:
 def __init__(self,dev:Device,phase:str,journal:C.Journal):self.dev=dev;self.phase=phase;self.journal=journal
 def call(self,op:str):self.dev.step(self.phase+':'+op)
 def healthy(self):self.call('healthy')
 def setup(self):self.call('setup');self.dev.staged={}
 def stage(self,kind:str,data:bytes):self.call('stage_'+kind);self.dev.staged[kind]=data
 def read(self)->bytes:self.call('read');return self.dev.block
 def write(self,kind:str):
  # Dispatch may partially change storage before loss of completion evidence.
  self.dev.writes.append(kind);self.dev.block=self.dev.staged[kind]
  self.call('write_'+kind)
 def cleanup(self):self.call('cleanup');self.dev.staged={}
 def safety_snapshot(self,expected:str|tuple[str,...],manifest:dict):
  self.call('snapshot')
  allowed=(expected,) if isinstance(expected,str) else expected
  F.require(F.sha(self.dev.block) in allowed,'fixture full partition mismatch')

class FakeHost:
 def __init__(self,dev:Device,delivery='completion_unconfirmed'):
  self.dev=dev;self.delivery=delivery;self.boot=OLD;self.tid='1';self.entries=0;self.tcp=0
 def inventory(self,timeout=8):self.dev.step('host:inventory');return [row(tid=self.tid)]
 def stock_snapshot(self,r,timeout=8):self.dev.step('host:snapshot');return snapshot(self.boot)
 def entry(self,pin):
  self.entries+=1;self.dev.step('host:entry');return dict(delivery=self.delivery,requests=1)
 def ensure_tcp(self,pin,returned):self.tcp+=1;self.dev.step('host:ensure_tcp')

class FakeObserver:
 def __init__(self,host:FakeHost,pin:dict,run:str,nonce:str,directory:Path,*,behavior='return',classification='diagnostic_pass'):
  self.host=host;self.pin=pin;self.behavior=behavior;self.classification=classification
  self.state=dict(diagnostic_seen=False,stock_returned=False,error=None)
 def start(self):
  self.host.dev.step('observer:start')
  if self.behavior=='not_ready':raise F.Refused('observer never ready')
  if self.behavior=='ready_timeout':raise F.Unknown('observer readiness timeout')
 def arm(self):self.host.dev.step('observer:arm')
 def stop(self):pass
 def wait(self):
  self.host.dev.step('observer:wait')
  new=self.behavior not in ('timeout','same_boot','malformed_return')
  s=snapshot(NEW if new else OLD);self.host.boot=s['boot_id'];self.host.tid='3'
  return dict(diagnostic_pass=self.classification=='diagnostic_pass',report_classification=self.classification,
   stock_returned=self.behavior not in ('timeout','same_boot'),error=None,
   stock_return=dict(row=row(tid='3'),snapshot=s),return_timing_consistent_with_120s_deadline=self.behavior!='early')

class Base(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(prefix='fault-',dir=S/'tests');self.root=Path(self.tmp.name)
  self.stack=contextlib.ExitStack()
  for obj,name,value in ((E,'SIZE',1024),(E,'STOCK_HASH',F.sha(STOCK)),(F,'SIZE',1024),
      (F,'STOCK_SHA',F.sha(STOCK)),(F,'FULL_SHA',F.sha(CANDIDATE))):
   self.stack.enter_context(patch.object(obj,name,value))
 def tearDown(self):self.stack.close();self.tmp.cleanup()
 def trial(self,*,fault=None,kind='uncertain',behavior='return',classification='diagnostic_pass',delivery='completion_unconfirmed',recheck=None):
  d=Device(fault=fault,fault_kind=kind);host=FakeHost(d,delivery);state=C.RunState(self.root,RUN,'trial','OFFLINE_FIXTURE')
  def factory(root,run,phase,action,boot,host):
   directory=C.phase_directory(root,phase);j=C.Journal(directory,action,'OFFLINE_FIXTURE')
   return MemoryTransport(d,phase,j),j
  def obs(*args):return FakeObserver(*args,behavior=behavior,classification=classification)
  with patch.object(C,'transport',side_effect=factory):
   result=C.run_trial(self.root,RUN,STOCK,CANDIDATE,host,state,{'contract':{'OFFLINE':True}},recheck or (lambda:None),observer_type=obs)
  self.assertEqual(d.para,b'unchanged para fixture');self.assertEqual(d.cache,b'unchanged cache fixture')
  self.assertLessEqual(d.writes.count('candidate'),1);self.assertLessEqual(d.writes.count('stock'),1)
  self.assertLessEqual(host.entries,1);self.assertLessEqual(result['entry_requests'],1)
  RESULTS.append(dict(case=self.id(),fault=fault,behavior=behavior,delivery=delivery,outcome=result['outcome'],
   writes=d.writes,calls=d.calls,entry_requests=result['entry_requests'],stock_returned=result['stock_returned'],
   p10_restored=result['p10_restored'],cleanup_verified=result['cleanup_verified'],metadata_reverified=result['metadata_reverified'],
   para_cache_fixture_unchanged=True,commands_after_transport_loss=None if d.lost_at is None else len(d.calls)-d.lost_at))
  return d,host,result

class ControllerTests(Base):
 def test_success(self):
  d,h,r=self.trial();self.assertEqual(d.writes,['candidate','stock']);self.assertEqual(d.block,STOCK)
  self.assertEqual(r['outcome'],'diagnostic_pass_stock_return_and_p10_restore_verified');self.assertTrue(r['metadata_reverified'])
  self.assertFalse(r['timer_firing_physically_proved']);self.assertEqual(r['entry_intents'],1)
  self.assertLess(d.calls.index('observer:arm'),d.calls.index('host:entry'))
 def test_missing_and_bad_report_still_restore_but_never_pass(self):
  for c in ('not_observed','partial','invalid'):
   with self.subTest(c=c):
    sub=self.root/c;sub.mkdir();old=self.root;self.root=sub
    d,h,r=self.trial(classification=c);self.root=old
    self.assertEqual(d.writes,['candidate','stock']);self.assertFalse(r['diagnostic_pass'])
    self.assertEqual(r['outcome'],'stock_return_and_restore_verified_diagnostic_incomplete')
 def test_no_return_and_same_boot_no_inverse(self):
  for behavior in ('timeout','same_boot','malformed_return'):
   with self.subTest(behavior=behavior):
    sub=self.root/behavior;sub.mkdir();old=self.root;self.root=sub
    d,h,r=self.trial(behavior=behavior);self.root=old
    self.assertEqual(d.writes,['candidate']);self.assertFalse(r['stock_returned']);self.assertEqual(h.tcp,0)
 def test_observer_not_ready_known_failure_one_inverse_no_entry(self):
  d,h,r=self.trial(behavior='not_ready');self.assertEqual(d.writes,['candidate','stock']);self.assertEqual(h.entries,0)
  self.assertEqual(r['entry_delivery']['delivery'],'not_issued');self.assertEqual(r['entry_intents'],0)
 def test_observer_timeout_no_inverse(self):
  d,h,r=self.trial(behavior='ready_timeout');self.assertEqual(d.writes,['candidate']);self.assertEqual(h.entries,0)
  self.assertEqual(r['outcome'],'transport_uncertain_no_retry')
 def test_unknown_entry_observes_but_never_mutates_even_with_new_stock(self):
  d,h,r=self.trial(delivery='unknown');self.assertTrue(r['stock_returned']);self.assertEqual(h.tcp,0)
  self.assertEqual(d.writes,['candidate']);self.assertEqual(r['outcome'],'entry_transport_uncertain_observed_no_mutation_stop')
 def test_explicit_service_failure_same_boot_is_not_return(self):
  d,h,r=self.trial(delivery='explicit_service_failure',behavior='same_boot')
  self.assertEqual(d.writes,['candidate']);self.assertEqual(h.entries,1);self.assertFalse(r['stock_returned'])
 def test_early_return_not_timer_proof(self):
  d,h,r=self.trial(behavior='early');self.assertTrue(r['stock_returned']);self.assertTrue(r['p10_restored'])
  self.assertEqual(r['outcome'],'stock_return_and_restore_verified_diagnostic_incomplete')
 def test_completed_candidate_write_failure_uses_only_engine_inverse(self):
  d,h,r=self.trial(fault='install:write_candidate',kind='failed')
  self.assertEqual(d.writes,['candidate','stock']);self.assertEqual(h.entries,0);self.assertTrue(r['p10_restored'])
 def test_completed_inverse_failure_not_retried(self):
  d,h,r=self.trial(fault='restore:write_stock',kind='failed')
  self.assertEqual(d.writes,['candidate','stock']);self.assertFalse(r['p10_restored']);self.assertEqual(r['outcome'],'stock_returned_restore_unverified_stop')
 def test_metadata_refusal_before_inverse_stops(self):
  d,h,r=self.trial(fault='restore-guard:snapshot',kind='refused')
  self.assertTrue(r['stock_returned']);self.assertEqual(d.writes,['candidate']);self.assertFalse(r['p10_restored'])
 def test_metadata_failure_after_restore_preserves_truth(self):
  d,h,r=self.trial(fault='restore-verification:snapshot',kind='refused')
  self.assertTrue(r['p10_restored']);self.assertFalse(r['metadata_reverified']);self.assertNotEqual(r['outcome'],'diagnostic_pass_stock_return_and_p10_restore_verified')
 def test_expired_review_after_entry_no_tcp_or_restore(self):
  calls=0
  def check():
   nonlocal calls
   calls+=1
   if calls>=3:raise F.Refused('fixture expired review')
  d,h,r=self.trial(recheck=check);self.assertTrue(r['stock_returned']);self.assertEqual(h.tcp,0);self.assertEqual(d.writes,['candidate'])
 def test_inverse_single_use(self):
  state=C.RunState(self.root,RUN,'trial','OFFLINE');state.data['restore_started']=True
  with self.assertRaises(F.Refused):C.restore_once(self.root,RUN,STOCK,NEW,FakeHost(Device()),state,lambda:None)

# Each phase boundary is a separate unittest case with a concrete recorded trace.
LOSS_POINTS=['preflight:snapshot','install:healthy#1','install:setup','install:stage_stock','install:stage_candidate',
 'install:read#1','install:healthy#2','install:write_candidate','install:read#2','install:healthy#3',
 'install:cleanup','install:healthy#4','entry-guard:snapshot','observer:start','observer:arm',
 'host:entry','observer:wait','host:ensure_tcp','restore-guard:snapshot','restore:healthy#1',
 'restore:setup','restore:stage_stock','restore:read#1','restore:healthy#2','restore:write_stock',
 'restore:read#2','restore:healthy#3','restore:cleanup','restore:healthy#4','restore-verification:snapshot']
def loss_test(point):
 def test(self):
  d,h,r=self.trial(fault=point)
  self.assertIsNotNone(d.lost_at,point);self.assertEqual(len(d.calls),d.lost_at,point)
  self.assertNotEqual(r['outcome'],'diagnostic_pass_stock_return_and_p10_restore_verified')
  if point=='host:entry':self.assertEqual(r['entry_delivery']['delivery'],'possible_dispatch')
 return test
for i,point in enumerate(LOSS_POINTS):setattr(ControllerTests,f'test_loss_{i:02d}_{point.replace(":","_").replace("#","_")}',loss_test(point))

class GateTests(Base):
 def test_all_actions_default_plan_no_host(self):
  for action in ('plan','preflight','trial'):
   d=self.root/action;d.mkdir()
   with patch.object(C,'new_run',return_value=(d,RUN)),patch.object(F,'fixed_inputs',return_value=(STOCK,CANDIDATE,[])),patch.object(C,'HostIO',side_effect=AssertionError('host in plan')),contextlib.redirect_stdout(io.StringIO()):
    self.assertEqual(C.main([action]),0)
   saved=json.loads((d/'state.json').read_text());self.assertFalse(saved['device_contacted']);self.assertEqual(saved['entry_requests'],0)
   self.assertFalse(json.loads((d/'review-template.json').read_text())['parent_review']['approved'])
 def test_cli_gate_refuses_without_device(self):
  for i,args in enumerate((['plan','--execute'],['trial','--execute'],['trial','--execute','--unattended-stock-only','--exclusive-device-owner'])):
   d=self.root/str(i);d.mkdir()
   with patch.object(C,'new_run',return_value=(d,RUN)),patch.object(F,'fixed_inputs',return_value=(STOCK,CANDIDATE,[])),patch.object(C,'HostIO',side_effect=AssertionError('host before gates')),contextlib.redirect_stdout(io.StringIO()):
    self.assertEqual(C.main(args),2)
 def test_lock_contention_and_review_replay(self):
  d=self.root/'run';d.mkdir();lockpath=self.root/'execute.lock'
  (self.root/'evidence/service').mkdir(parents=True)
  with lockpath.open('a') as lock:
   fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
   with patch.object(E,'EXECUTE_LOCK',lockpath),patch.object(C,'new_run',return_value=(d,RUN)),patch.object(F,'fixed_inputs',return_value=(STOCK,CANDIDATE,[])),patch.object(C,'review',return_value={}),patch.object(C,'HostIO',side_effect=AssertionError('locked host')),contextlib.redirect_stdout(io.StringIO()):
    self.assertEqual(C.main(['trial','--execute','--unattended-stock-only','--exclusive-device-owner']),2)
  with patch.object(F,'S',self.root):
   C.consume_review('a'*64,RUN)
   with self.assertRaises(FileExistsError):C.consume_review('a'*64,RUN)
 def test_review_schema_pins_and_window(self):
  value=C.template();r=value['parent_review']
  for k,v in r.items():
   if isinstance(v,bool):r[k]=True
  r.update(reviewer='OFFLINE FIXTURE ONLY',reviewed_at_utc='2026-11-06T20:00:00+00:00')
  p=self.root/'review-FIXTURE.json'
  def check(v,now=dt.datetime(2026,11,6,20,1,tzinfo=dt.timezone.utc)):
   p.write_text(json.dumps(v));return C.review(p,F.sha(p.read_bytes()),now)
  self.assertEqual(check(value),value)
  for name,change in [('unapproved',lambda v:v['parent_review'].update(approved=False)),
     ('candidate',lambda v:v['contract'].update(candidate_sha256='0'*64)),
     ('sourcepin',lambda v:v['contract']['source_and_evidence_sha256'].update(unknown='0'*64)),
     ('extended',lambda v:v['parent_review'].update(valid_until_utc='2026-11-07T00:00:00+00:00'))]:
   v=copy.deepcopy(value);change(v)
   with self.subTest(name=name),self.assertRaises(F.Refused):check(v)
  for now in (dt.datetime(2026,11,6,17,2,tzinfo=dt.timezone.utc),dt.datetime(2026,11,6,23,4,tzinfo=dt.timezone.utc)):
   with self.assertRaises(F.Refused):check(value,now)
  check(value)
  with self.assertRaises(F.Refused):C.review(p,'0'*64)
 def test_fresh_pin_refuses_identity_secure_adb_boot_and_staleness(self):
  h=FakeHost(Device());pin=O.make_pin(h,RUN,'nonce')
  O.validate_pin(pin,RUN,'nonce',pin['created_monotonic'])
  for change in (lambda p:p.update(run_id='wrong'),lambda p:p.update(process_nonce='other'),lambda p:p.update(created_monotonic=0),
    lambda p:p.update(candidate_full_sha256='0'*64),lambda p:p.update(kernel_sha256='0'*64),lambda p:p['stock_snapshot'].update({'ro.adb.secure':'0'}),
    lambda p:p['stock_snapshot'].update(enforce='Permissive'),lambda p:p['stock_snapshot'].update(flash_recovery='running'),lambda p:p.update(stock_boot_id=NEW)):
   p=copy.deepcopy(pin);change(p)
   with self.assertRaises(F.Refused):O.validate_pin(p,RUN,'nonce',time.monotonic())
 def test_fixed_acceptance_hash_is_real_receipt(self):
  self.assertEqual(F.sha(F.read(F.ACCEPTANCE)),F.ACCEPTANCE_SHA)

class Clock:
 def __init__(self):self.now=0.0
 def __call__(self):return self.now
class Event:
 def __init__(self,clock:Clock):self.clock=clock;self.flag=False
 def set(self):self.flag=True
 def is_set(self):return self.flag
 def wait(self,seconds):
  if not self.flag:self.clock.now+=seconds
  return self.flag
class TimelineHost:
 def __init__(self,clock:Clock,events:list[str],report_bytes:bytes):self.clock=clock;self.events=iter(events);self.current='initial';self.report_bytes=report_bytes;self.reports=0
 def inventory(self,timeout=8):
  self.current=next(self.events,'absent')
  if self.current=='absent':return []
  return [row(self.current=='diag',{'initial':'1','same':'3','new':'3','diag':'2','reused':'1'}.get(self.current,'4'))]
 def stock_snapshot(self,r,timeout=8):return snapshot(NEW if self.current in ('new','reused') else OLD)
 def report(self,r,timeout=12):self.reports+=1;return subprocess.CompletedProcess([],0,self.report_bytes,b'')

class ObserverTests(Base):
 def observe(self,events,report_bytes=None):
  clock=Clock();pin=O.make_pin(FakeHost(Device()),RUN,'nonce',clock=clock)
  host=TimelineHost(clock,events,valid_report() if report_bytes is None else report_bytes)
  obs=O.Observer(host,pin,RUN,'nonce',self.root/'obs',clock=clock)
  obs.ready=Event(clock);obs.armed=Event(clock);obs.cancelled=Event(clock)
  obs.armed.set();obs.entry_at=0;obs.end=420;obs.run()
  return obs.state,host
 def test_actual_observer_new_stock_return(self):
  s,h=self.observe(['initial','diag']+['absent']*60+['new'])
  self.assertTrue(s['diagnostic_pass']);self.assertTrue(s['stock_returned']);self.assertTrue(s['return_timing_consistent_with_120s_deadline'])
 def test_same_boot_after_disconnect_never_return(self):
  s,h=self.observe(['initial','absent']+['same']*215)
  self.assertFalse(s['stock_returned']);self.assertIsNone(s['error']);self.assertEqual(s['events'][-1]['kind'],'observation_deadline_no_reset_inferred')
 def test_reused_transport_rejected(self):
  s,h=self.observe(['initial','reused']);self.assertFalse(s['stock_returned']);self.assertIsNotNone(s['error'])
 def test_missing_report_new_return_still_observed(self):
  s,h=self.observe(['initial','new']);self.assertTrue(s['stock_returned']);self.assertFalse(s['diagnostic_pass'])
 def test_partial_report_retries_bounded_and_no_success(self):
  s,h=self.observe(['initial']+['diag']*220,valid_report().replace(b'END_DIAGNOSTIC',b''))
  self.assertEqual(h.reports,4);self.assertFalse(s['diagnostic_pass']);self.assertFalse(s['stock_returned']);self.assertEqual(s['report_classification'],'partial')
 def test_report_validation(self):
  good=valid_report();self.assertEqual(O.report(good,0)['classification'],'diagnostic_pass')
  cases=[(good,1),(b'',0),(good.replace(F.SERIAL.encode(),b'wrong'),0),(good.replace(b'rootfs / rootfs',b'/dev/block/mmcblk0p24 /cache ext4'),0),
   (good.replace(b'\n1\n',b'\n0\n'),0),(good+b'garbage',0),(good.replace(b'12.3 4.5',b'nan 4'),0),(good+b'END_DIAGNOSTIC\n',0),
   (good.replace(b'uid=2000',b'uid=0'),0),(b'\xff',0),(b'x'*(256*1024+1),0)]
  for data,rc in cases:self.assertNotEqual(O.report(data,rc)['classification'],'diagnostic_pass')
 def test_ambiguous_and_wrong_usb_refused(self):
  with self.assertRaises(O.IdentityError):O.usb_row([row(),row(True,'2')])
  with self.assertRaises(O.IdentityError):O.usb_row([dict(row(),usb='other')],{'usb':'fixture:1'})

class AdapterTests(Base):
 def test_command_timeout_no_retry_and_durable_intent(self):
  h=T.HostIO(self.root/'commands')
  with patch.object(T.subprocess,'run',side_effect=subprocess.TimeoutExpired(['FIXTURE'],1)) as process:
   with self.assertRaises(O.Unavailable):h.command(['FIXTURE'],timeout=1)
   self.assertEqual(process.call_count,1)
  self.assertEqual(json.loads((h.directory/'0001.json').read_text())['status'],'dispatched')
  self.assertEqual(json.loads((h.directory/'0001-result.json').read_text())['status'],'uncertain')
 def test_completion_journal_failure_is_uncertain(self):
  h=T.HostIO(self.root/'commands');real=F.durable
  def durable(path,*args,**kwargs):
   if path.name.endswith('-result.json'):raise OSError('fixture disk failure')
   return real(path,*args,**kwargs)
  with patch.object(T.subprocess,'run',return_value=subprocess.CompletedProcess([],0,b'',b'')) as process,patch.object(F,'durable',side_effect=durable):
   with self.assertRaises(O.Unavailable):h.command(['FIXTURE'])
   self.assertEqual(process.call_count,1)
 def test_tcp_requires_new_secure_healthy_usb_and_fixed_port(self):
  pin=O.make_pin(FakeHost(Device()),RUN,'nonce');returned={'row':row(tid='3'),'snapshot':snapshot(NEW)}
  h=T.HostIO(self.root/'commands')
  with patch.object(h,'command',side_effect=AssertionError('no command before proof')):
   with self.assertRaises(F.Refused):h.ensure_tcp(pin,{'snapshot':snapshot(OLD)})
  with patch.object(h,'inventory',return_value=[row(tid='3')]),patch.object(h,'stock_snapshot',return_value=snapshot(NEW)),patch.object(h,'command',side_effect=[
   subprocess.CompletedProcess([],0,b'restarting in TCP mode port: 5555\n',b''),
   subprocess.CompletedProcess([],0,('connected to '+F.ENDPOINT+'\n').encode(),b'')]) as command:
   h.ensure_tcp(pin,returned)
   self.assertEqual([c.args[0] for c in command.call_args_list],[['adb','-t','3','tcpip','5555'],['adb','connect',F.ENDPOINT]])
  with patch.object(h,'inventory',return_value=[row(tid='3')]),patch.object(h,'stock_snapshot',return_value=snapshot(NEW)),patch.object(h,'command',side_effect=O.Unavailable('fixture loss')) as command:
   with self.assertRaises(O.Unavailable):h.ensure_tcp(pin,returned)
   self.assertEqual(command.call_count,1)
 def test_tcp_wrong_identity_never_dispatches(self):
  pin=O.make_pin(FakeHost(Device()),RUN,'nonce');returned={'row':row(tid='3'),'snapshot':snapshot(NEW)}
  for change in (lambda s:s.update({'ro.adb.secure':'0'}),lambda s:s.update(boot_id=OLD),lambda s:s.update(enforce='Permissive')):
   s=snapshot(NEW);change(s);h=T.HostIO(self.root/str(len(list(self.root.iterdir()))))
   with patch.object(h,'inventory',return_value=[row(tid='3')]),patch.object(h,'stock_snapshot',return_value=s),patch.object(h,'command',side_effect=AssertionError('wrong identity')) as command:
    with self.assertRaises(F.Refused):h.ensure_tcp(pin,returned)
    command.assert_not_called()
 def test_actual_transport_root_includes_boot_id_and_fixed_block_guards(self):
  j=C.Journal(self.root,'restore','OFFLINE')
  class Capture:
   scripts:list[str]=[]
   def command(self,argv,*,script=None,**kwargs):
    self.scripts.append(script)
    import re
    token=re.search(r'ASUS_RECOVERY_RC_([0-9a-f]{32})=',script).group(1)
    return subprocess.CompletedProcess(argv,0,'ASUS_RECOVERY_RC_'+token+'=0\n','')
  host=Capture();t=T.Transport(self.root,j,'restore',RUN,'restore',NEW,host)
  t.write('stock')
  self.assertEqual(len(host.scripts),1)
  script=host.scripts[0]
  self.assertIn(E.DEVICE_GUARD,script);self.assertIn(NEW,script);self.assertIn(F.KERNEL_BANNER,script)
  self.assertIn('getprop init.svc.flash_recovery',script)
  import re
  self.assertEqual(re.findall(r'dd if=\S+ of=(\S+)',script),[E.BLOCK])
  self.assertNotIn('/cache/recovery/command',script)


class SafetyTransport(T.Transport):
 """Exercise actual snapshot/parser checks with fixture bytes, no shell interpreter."""
 def __init__(self,directory,journal,blobs,rc,block=STOCK):
  super().__init__(directory,journal,'install',RUN,'preflight',OLD,None);self.blobs=blobs;self.rc=rc;self.block=block;self.scripts=[]
 def healthy(self):pass
 def setup(self):self.stage_created=True
 def root(self,body,label):self.scripts.append((label,body))
 def pull_blob(self,name,limit):return self.rc if name=='rc.tar' else self.blobs[name]
 def blob(self,source,name,limit):return self.blobs[name]
 def read(self):return self.block
 def cleanup(self):self.stage_created=False

def archive(files):
 out=io.BytesIO()
 with tarfile.open(fileobj=out,mode='w') as tar:
  for name,data in files:
   info=tarfile.TarInfo(name);info.size=len(data);tar.addfile(info,io.BytesIO(data))
 return out.getvalue()
class SafetyTests(Base):
 def test_actual_snapshot_firmware_rc_para_p10_mismatch(self):
  blobs={'para.bin':b'para','init.bin':b'init','adbd.bin':b'adbd'};manifest={'/init.rc':{'sha256':F.sha(b'rc')}}
  with patch.object(F,'PARA_SIZE',4),patch.object(F,'PARA_SHA',F.sha(b'para')),patch.object(F,'INIT_SHA',F.sha(b'init')),patch.object(F,'ADBD_SHA',F.sha(b'adbd')):
   for name in ('valid','para.bin','init.bin','adbd.bin','rc_hash','rc_extra','rc_duplicate','p10'):
    with self.subTest(name=name):
     d=self.root/name;d.mkdir();j=C.Journal(d,'install','OFFLINE');b=dict(blobs)
     if name in b:b[name]=b'BAD'
     files=[('init.rc',b'wrong' if name=='rc_hash' else b'rc')]
     if name=='rc_extra':files.append(('extra.rc',b'extra'))
     if name=='rc_duplicate':files.append(('init.rc',b'rc'))
     t=SafetyTransport(d,j,b,archive(files),CANDIDATE if name=='p10' else STOCK)
     if name=='valid':
      t.safety_snapshot(F.STOCK_SHA,manifest)
      self.assertEqual(j.state['events'][-1]['kind'],'fresh_stock_safety_snapshot')
     else:
      with self.assertRaises(F.Refused):t.safety_snapshot(F.STOCK_SHA,manifest)
     for label,script in t.scripts:
      self.assertNotIn('of=/dev/block/mmcblk0p12',script);self.assertNotIn('of=/dev/block/mmcblk0p24',script)
      self.assertNotIn('rm /cache',script)
 def test_entry_delivery_actual_adapter(self):
  for i,(out,rc,err,expected) in enumerate(((b'',0,b'','completion_unconfirmed'),(b'reboot failed: -1\n',1,b'','explicit_service_failure'),(b'',1,b'closed','completion_unconfirmed'))):
   h=T.HostIO(self.root/str(i))
   with patch.object(h,'command',return_value=subprocess.CompletedProcess([],rc,out,err)) as call:
    r=h.entry({'initial_transport_id':'1'});self.assertEqual(r['delivery'],expected);self.assertEqual(call.call_count,1)
  h=T.HostIO(self.root/'uncertain')
  with patch.object(h,'command',side_effect=O.Unavailable('lost')) as call:
   self.assertEqual(h.entry({'initial_transport_id':'1'})['delivery'],'unknown');self.assertEqual(call.call_count,1)
 def test_root_completion_provenance(self):
  token='a'*32
  for rc,out in ((0,''),(1,f'ASUS_RECOVERY_RC_{token}=0\n'),(0,f'ASUS_RECOVERY_RC_{token}=0\n'*2)):
   with self.assertRaises(E.UncertainTransport):E.root_status(subprocess.CompletedProcess([],rc,out,''),token)
  self.assertEqual(E.root_status(subprocess.CompletedProcess([],0,f'ASUS_RECOVERY_RC_{token}=23\n',''),token),23)

if __name__=='__main__':
 os.umask(0o077)
 suite=unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]);stream=io.StringIO()
 result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite);text=stream.getvalue();print(text,end='')
 out=S/'evidence/service';out.mkdir(parents=True,exist_ok=True)
 stamp=dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
 (out/('fault-suite-'+stamp+'.txt')).write_text(text)
 F.durable(out/('fault-suite-'+stamp+'.json'),dict(device_contacted=False,tests_run=result.testsRun,
  failures=len(result.failures),errors=len(result.errors),status='PASS' if result.wasSuccessful() else 'FAIL',
  limits='Typed byte-storage/transport fixtures and actual Python controller/engine/observer. No Android kernel, shell, device, or PMIC execution.',scenarios=RESULTS),exclusive=True)
 raise SystemExit(0 if result.wasSuccessful() else 1)
