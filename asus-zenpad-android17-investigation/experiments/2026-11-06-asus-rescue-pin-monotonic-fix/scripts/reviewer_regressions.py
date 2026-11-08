#!/usr/bin/env python3
"""Independent bounded fixture tests; no real process or network operations allowed."""
import sys
from pathlib import Path
import io,json,os,time,unittest,contextlib,copy
ROOT=Path(__file__).resolve().parents[1]
SNAP=ROOT
BLOCKED=[]
def audit(event,args):
    if event in {'subprocess.Popen','os.system','os.posix_spawn','os.fork','os.forkpty','os.exec','pty.spawn'} or event.startswith('socket.'):
        BLOCKED.append(event)
        raise AssertionError('OFFLINE AUDIT: '+event)
sys.addaudithook(audit)
sys.path[:0]=[str(SNAP/'source'),str(SNAP/'tests')]
import test_adapter as supplied
from unittest.mock import patch
import subprocess
import adapter as a
b=a.b
OBS=[]
OUT=ROOT/'evidence'/('targeted-'+str(time.time_ns()))
OUT.mkdir(exist_ok=False)

class Review(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stock,cls.full,cls.local=a.verify_local()
    def setUp(self):
        self.directory=OUT/self._testMethodName
        self.directory.mkdir()
        self.fake=supplied.Fake(self.stock)
        self.code=a.code_receipt()['sha256']
    def transport(self,phase='install',pin=None,contract=None):
        pin=supplied.pin() if pin is None else pin
        contract=supplied.contract(phase) if contract is None else contract
        guard=a.Guard(contract,supplied.RUN,phase,self.code,pin)
        j=a.Journal(self.directory,phase,supplied.RUN,self.code)
        j.state['pin']=pin;j.save()
        return a.Transport(self.directory,j,phase,guard)
    def remember(self,**fields):
        OBS.append(dict(test=self._testMethodName,**fields))
        (self.directory/'observations.json').write_text(json.dumps(OBS[-1],indent=2)+'\n')
    def test_pin_monotonic_age_expires_before_candidate_write(self):
        clock={'wall':2000000000.0,'mono':1000.0}
        with patch.object(time,'time',side_effect=lambda:clock['wall']),patch.object(time,'monotonic',side_effect=lambda:clock['mono']):
            p=supplied.pin();c=supplied.contract('install');c['valid_until']=clock['wall']+590
            t=self.transport(pin=p,contract=c)
            # Complete staging and actual full stock observation while the pin is fresh.
            with patch.object(subprocess,'run',side_effect=self.fake):
                t.setup();t.stage('stock',self.stock);t.stage('candidate',self.full);t.read()
                # Real elapsed time 200 s; a 100 s clock correction leaves wall age at 100 s.
                clock.update(wall=2000000100.0,mono=1200.0)
                error=None
                try:t.write('candidate')
                except b.UncertainTransport as exc:error=str(exc)
            writes=copy.deepcopy(self.fake.inner.writes)
            self.remember(wall_pin_age=clock['wall']-p['created_at'],monotonic_pin_age=200,
                          contract_remaining_monotonic=t.guard.end_mono-clock['mono'],
                          writes=writes,error=error,stopped=t.guard.stopped)
            self.assertEqual(writes,[], '180-second pin expired in monotonic time; actual nested writer still admitted')
    def test_reloaded_pin_expired_monotonically_refused_before_commands(self):
        clock={'wall':2000000000.0,'mono':1000.0}
        with patch.object(time,'time',side_effect=lambda:clock['wall']),patch.object(time,'monotonic',side_effect=lambda:clock['mono']),patch.object(a,'RUNS',self.directory/'runs'):
            directory=a.reserve(supplied.RUN,'pin-install')
            guard=a.Guard(supplied.contract('pin-install'),supplied.RUN,'pin-install',self.code)
            journal=a.Journal(directory,'pin-install',supplied.RUN,self.code)
            transport=a.Transport(directory,journal,'pin-install',guard)
            with patch.object(subprocess,'run',side_effect=self.fake):p=transport.usb_snapshot()
            a.durable(directory/'pin.json',p)
            journal.finish('healthy_stock_usb_pin_captured',pin=p,pin_sha256=a.object_sha(p))
            clock.update(wall=2000000100.0,mono=1400.0)
            # Reload the actual serialized pin through the production admission path.
            accepted=None;error=None
            try:accepted=a.load_pin(supplied.RUN,'install',self.code)
            except b.Refused as exc:error=str(exc)
            self.remember(wall_pin_age=100,monotonic_pin_age=400,actual_usb_capture_commands=len(self.fake.calls),
                          accepted_reloaded_pin=accepted is not None,error=error)
            self.assertIsNone(accepted, 'Production load_pin accepted its own serialized pin after 400 elapsed seconds')
    def test_contract_monotonic_expiry_stops_actual_nested_root_binary_push(self):
        t=self.transport();durable=a.durable
        def expire(path,value):
            durable(path,value)
            if value.get('argv')==['adb','-s',b.ENDPOINT,'push',str(b.ROOT_BINARY),'/data/local/tmp/asus-mtk-su64']:
                t.guard.end_mono=time.monotonic()-1
        with patch.object(a,'durable',side_effect=expire),patch.object(subprocess,'run',side_effect=self.fake),self.assertRaises(b.UncertainTransport):t.setup()
        self.assertFalse(any(argv[3:4]==['push'] for argv,_ in self.fake.calls))
        n=len(self.fake.calls)
        with patch.object(subprocess,'run',side_effect=self.fake),self.assertRaises(b.UncertainTransport):t.write('stock')
        self.assertEqual(n,len(self.fake.calls))
    def test_missing_operation_status_is_terminal_through_production_execute(self):
        t=self.transport();self.fake.inner.fault='missing_status'
        with patch.object(subprocess,'run',side_effect=self.fake):
            state=a.execute('install',self.stock,self.full,t,t.journal)
        self.assertEqual(state['outcome'],'terminal_uncertainty_no_commands')
        self.assertTrue(t.guard.stopped)
        self.assertEqual([w['source'] for w in self.fake.inner.writes],['candidate'])
        n=len(self.fake.calls)
        with patch.object(subprocess,'run',side_effect=self.fake),self.assertRaises(b.UncertainTransport):t.cleanup()
        self.assertEqual(n,len(self.fake.calls))
    def test_candidate_completion_persistence_failure_forbids_inverse_and_cleanup(self):
        t=self.transport();durable=a.durable;trip=[]
        def loss(path,value):
            if value.get('status')=='returned' and value.get('stdin') and 'dd if='+t.vault+'/candidate.bin of='+b.BLOCK in value['stdin']:
                trip.append(len(self.fake.calls));raise OSError('fixture completion publication EIO')
            durable(path,value)
        with patch.object(a,'durable',side_effect=loss),patch.object(subprocess,'run',side_effect=self.fake):
            state=a.execute('install',self.stock,self.full,t,t.journal)
        self.assertEqual(state['outcome'],'terminal_uncertainty_no_commands')
        self.assertEqual(len(self.fake.calls),trip[0]);self.assertTrue(state['partition_may_be_modified'])
        self.assertEqual([w['source'] for w in self.fake.inner.writes],['candidate'])
    def test_unhealthy_known_candidate_failure_does_not_inverse(self):
        t=self.transport();self.fake.inner.fault='unhealthy_after_failure'
        with patch.object(subprocess,'run',side_effect=self.fake):state=a.execute('install',self.stock,self.full,t,t.journal)
        self.assertEqual(state['outcome'],'inverse_unverified_stop')
        self.assertEqual([w['source'] for w in self.fake.inner.writes],['candidate'])
        self.assertTrue(t.guard.stopped)
    def test_restore_full_readback_mismatch_keeps_modified_and_does_not_retry(self):
        t=self.transport('restore');self.fake=supplied.Fake(self.full,'restore_mismatch')
        with patch.object(subprocess,'run',side_effect=self.fake):state=a.execute('restore',self.stock,self.full,t,t.journal)
        self.assertEqual(state['outcome'],'refused_or_failed_stop')
        self.assertTrue(state['partition_may_be_modified']);self.assertFalse(state['restore_verified'])
        self.assertEqual([w['source'] for w in self.fake.inner.writes],['stock'])
    def test_duplicate_candidate_and_inverse_dispatch_are_consumed(self):
        t=self.transport()
        with patch.object(subprocess,'run',side_effect=self.fake):
            t.setup();t.stage('candidate',self.full);t.stage('stock',self.stock);t.write('candidate');t.write('stock')
            with self.assertRaises(b.UncertainTransport):t.write('stock')
        self.assertTrue(t.guard.stopped)
        self.assertEqual([w['source'] for w in self.fake.inner.writes],['candidate','stock'])
    def test_helper_uses_only_isolated_module_references(self):
        t=self.transport();run=subprocess.run;stdout=sys.stdout;stderr=sys.stderr
        with patch.object(subprocess,'run',side_effect=self.fake) as patched:
            t.setup()
            self.assertIs(subprocess.run,patched)
            self.assertIs(sys.stdout,stdout);self.assertIs(sys.stderr,stderr)
        self.assertIs(subprocess.run,run)

stream=io.StringIO();suite=unittest.defaultTestLoader.loadTestsFromTestCase(Review)
result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
(OUT/'tests.txt').write_text(stream.getvalue())
receipt=dict(tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),
 failure_details=[dict(test=str(t),traceback=s) for t,s in result.failures],
 error_details=[dict(test=str(t),traceback=s) for t,s in result.errors],
 observations=OBS,audit_blocked_events=BLOCKED,actual_subprocess_calls=0,
 code=a.code_receipt(),device_contacted=False,network_operations=0,
 limits='Typed storage/transport fakes; exact production code unmodified. No physical/runtime proof.')
(OUT/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(stream.getvalue());print(json.dumps(dict(evidence=str(OUT),**{k:receipt[k] for k in ('tests','failures','errors','audit_blocked_events')})))
raise SystemExit(0 if result.wasSuccessful() and not BLOCKED else 1)
