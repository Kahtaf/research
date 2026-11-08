"""Offline review probes. Imports pinned production; forbids all subprocess/network effects."""
import sys
sys.dont_write_bytecode=True
import ast, hashlib, importlib.util, io, json, re, subprocess, types, unittest
from pathlib import Path
from unittest.mock import patch
R=Path(__file__).resolve().parents[2]
P=R
for name,digest in json.loads((P/'evidence/source-pins-r2.json').read_text()).items():
    assert hashlib.sha256((P/name).read_bytes()).hexdigest()==digest,name
sys.path.insert(0,str(P/'source/service'))
import controller as C, transport as T, fixed as F, root_dispatch as D, observer as O
spec=importlib.util.spec_from_file_location('review_fixtures',R/'tests/service/test_faults.py')
M=importlib.util.module_from_spec(spec);sys.modules[spec.name]=M;spec.loader.exec_module(M)
E=F.E
RECORDS=[]

def answer(argv,script,stderr=''):
    args=argv[3:];out=''
    if args==['get-serialno']:out=F.ENDPOINT+'\n'
    elif args[:2]==['shell','getprop']:out=F.STOCK_PROPS[args[2]]+'\n'
    elif args==['shell','getenforce']:out='Enforcing\n'
    elif script:
        inner=re.search(r'ASUS_RECOVERY_RC_([0-9a-f]{32})=',script).group(1)
        outer=re.search(r'ASUS_WIFI_ROOT_([0-9a-f]{32})=',script).group(1)
        out='ASUS_RECOVERY_RC_'+inner+'=0\nASUS_WIFI_ROOT_'+outer+'=0\n'
    return subprocess.CompletedProcess(argv,0,out,stderr)

def helper(host,check=lambda:None):
    return D.run([sys.executable,str(E.HELPER)],E.root_envelope('FIXTURE_ONLY', 'a'*32),host,check)

class Review(M.Base):
    def test_intent_expiry_all_thirteen_actual_boundaries(self):
        for boundary in range(1,14):
            host=T.HostIO(self.root/str(boundary));calls=[];expired=[False];saved=F.durable
            def durable(path,*a,**kw):
                result=saved(path,*a,**kw)
                if path==host.directory/f'{boundary:04}.json':expired[0]=True
                return result
            def check():
                self.assertTrue((host.directory/f'{host.sequence:04}.json').exists())
                if expired[0]:raise F.AuthorizationExpired('expiry at durable intent')
            def process(argv,**kw):
                self.assertFalse(expired[0]);calls.append((argv,kw));return answer(argv,kw.get('input'))
            with patch.object(F,'durable',side_effect=durable),patch.object(T,'subprocess',types.SimpleNamespace(run=process,TimeoutExpired=subprocess.TimeoutExpired)):
                with self.assertRaises(F.AuthorizationExpired):helper(host,check)
            self.assertEqual(len(calls),boundary-1)
            self.assertEqual(json.loads((host.directory/f'{boundary:04}-result.json').read_text())['status'],'authorization_expired_before_dispatch')
            RECORDS.append(dict(probe='intent_expiry',boundary=boundary,dispatches=len(calls)))

    def test_old_precheck_boundary_and_inflight_root_controller_no_inverse(self):
        for expire_at in (9,12):
            old=self.root;self.root=old/str(expire_at);self.root.mkdir()
            host=T.HostIO(self.root/'nested');calls=[];expired=[False];real_write=M.MemoryTransport.write
            def check():
                if expired[0]:raise F.AuthorizationExpired('nested request completed after expiry')
            def write(t,kind):
                if t.phase!='install':return real_write(t,kind)
                def process(argv,**kw):
                    calls.append((argv,kw))
                    if kw.get('input') is not None:real_write(t,kind)
                    if len(calls)==expire_at:expired[0]=True
                    return answer(argv,kw.get('input'))
                with patch.object(T,'subprocess',types.SimpleNamespace(run=process,TimeoutExpired=subprocess.TimeoutExpired)):
                    helper(host,check)
            with patch.object(M.MemoryTransport,'write',write):dev,h,result=self.trial(recheck=check)
            self.assertEqual(len(calls),expire_at)
            self.assertEqual(dev.writes,[] if expire_at==9 else ['candidate'])
            self.assertEqual(result['outcome'],'authorization_expired_no_new_command')
            self.assertTrue(result['partition_may_be_modified']);self.assertEqual(h.entries,0)
            self.assertFalse(any(x.startswith('restore') for x in dev.calls))
            if expire_at==12:
                self.assertIn("trap 'setenforce 1' EXIT",calls[-1][1]['input'])
                self.assertEqual(calls[-1][1]['timeout'],75)
                self.assertEqual(json.loads((host.directory/'0012-result.json').read_text())['status'],'returned')
            RECORDS.append(dict(probe='integrated_nested_expiry',expire_after=expire_at,dispatches=len(calls),writes=dev.writes,outcome=result['outcome']))
            self.root=old

    def test_timeout_identity_status_and_no_global_mutation(self):
        for case in ('normal','identity','precheck','push','chmod','enforcing','missing','duplicate','disagree','timeout'):
            host=T.HostIO(self.root/case);calls=[]
            refs=(subprocess.run,subprocess.check_output,sys.stdin,sys.stdout,sys.stderr,sys.argv)
            def process(argv,**kw):
                calls.append((argv,kw));n=len(calls);p=answer(argv,kw.get('input'))
                if case=='identity' and n==2:p.stdout='WRONG\n'
                if (case,n) in [('precheck',9),('push',10),('chmod',11)]:p.returncode=1
                if case=='enforcing' and n==13:p.stdout='Permissive\n'
                if n==12:
                    if case=='missing':p.stdout=''
                    if case=='duplicate':p.stdout+=p.stdout
                    if case=='disagree':p.returncode=1
                    if case=='timeout':raise subprocess.TimeoutExpired(argv,75)
                return p
            with patch.object(T,'subprocess',types.SimpleNamespace(run=process,TimeoutExpired=subprocess.TimeoutExpired)):
                if case=='normal':
                    p=helper(host);self.assertEqual(E.root_status(p,'a'*32),0)
                    self.assertEqual([kw['timeout'] for _,kw in calls],[12]*9+[20,12,75,12])
                else:
                    with self.assertRaises(O.Unavailable):helper(host)
            self.assertEqual(refs,(subprocess.run,subprocess.check_output,sys.stdin,sys.stdout,sys.stderr,sys.argv))
            self.assertTrue(all(a[:3]==['adb','-s',F.ENDPOINT] for a,_ in calls))
            RECORDS.append(dict(probe='helper_failure',case=case,dispatches=len(calls)))

    def test_raw_entry_matrix_with_real_host_journal_and_integrated_unknown(self):
        failure=b'reboot failed: -1\n'
        cases=[(0,b'',b''),(0,failure,b''),(1,failure,b''),(1,b'reboot failed: -1\r\n',b''),
            (1,b' \t\n'+failure+b'\n\x0b',b''),(1,b'\xc2\xa0'+failure,b''),
            (1,b'\xff'+failure,b''),(1,failure+b'\xff',b''),(1,failure[:-1],b''),
            (1,failure*2,b''),(1,b'',b'error: closed\n'),(-9,b'',b''),
            (-9,failure,b''),(0,b'unexpected\n',b''),(1,failure,b'warning'),(1,b'reboot failed: -1\r',b'')]
        for i,(rc,out,err) in enumerate(cases):
            old=self.root;self.root=old/str(i);self.root.mkdir()
            adapter=T.HostIO(self.root/'commands');adapter.authorization_check=lambda:None
            def entry(h,pin):
                h.entries+=1
                with patch.object(T,'subprocess',types.SimpleNamespace(run=lambda *a,**k:subprocess.CompletedProcess([],rc,out,err),TimeoutExpired=subprocess.TimeoutExpired)):
                    return adapter.entry(pin)
            with patch.object(M.FakeHost,'entry',entry):dev,h,r=self.trial()
            delivery=r['entry_delivery'];expected='completion_unconfirmed' if i==0 else 'explicit_service_failure' if i<4 else 'unknown'
            self.assertEqual(delivery['delivery'],expected)
            self.assertEqual(delivery['stdout_hex'],out.hex());self.assertEqual(delivery['stderr_hex'],err.hex())
            saved=json.loads((adapter.directory/'0001-result.json').read_text())
            self.assertEqual(saved['stdout_hex'],out.hex());self.assertEqual(saved['stderr_hex'],err.hex())
            if expected=='unknown':
                self.assertTrue(r['stock_returned']);self.assertEqual(h.tcp,0);self.assertEqual(dev.writes,['candidate'])
            RECORDS.append(dict(probe='entry',rc=rc,stdout_hex=out.hex(),stderr_hex=err.hex(),delivery=expected,tcp=h.tcp,writes=dev.writes))
            self.root=old

    def test_preentry_inverse_original_and_extended_exception_matrix(self):
        exceptions=[E.UncertainTransport,E.Refused,E.OperationFailed,E.VerificationFailed,O.Unavailable,OSError]
        for cls in exceptions:
            old=self.root;self.root=old/cls.__name__;self.root.mkdir();real=M.MemoryTransport.safety_snapshot
            def snapshot(t,*args):
                if t.phase=='restore-guard':raise cls('fixture')
                return real(t,*args)
            with patch.object(M.MemoryTransport,'safety_snapshot',snapshot):dev,h,r=self.trial(behavior='not_ready')
            self.assertTrue(r['partition_may_be_modified']);self.assertEqual(dev.writes,['candidate']);self.assertEqual(h.entries,0)
            RECORDS.append(dict(probe='inverse_exception',exception=cls.__name__,modified=r['partition_may_be_modified']))
            self.root=old

    def test_decode_error_in_preentry_inverse_is_terminal_and_preserves_modified(self):
        """Regression: unknown completion remains terminal."""
        real=M.MemoryTransport.safety_snapshot;host=T.HostIO(self.root/'nested');calls=[]
        def process(argv,**kw):
            calls.append(argv)
            return b'\xff'.decode('utf-8')
        def snapshot(t,*args):
            if t.phase=='restore-guard':
                with patch.object(T,'subprocess',types.SimpleNamespace(run=process,TimeoutExpired=subprocess.TimeoutExpired)):
                    helper(host)
            return real(t,*args)
        with patch.object(M.MemoryTransport,'safety_snapshot',snapshot):
            dev,h,r=self.trial(behavior='not_ready')
        saved=json.loads((self.root/'state.json').read_text())
        self.assertEqual(saved['install_result']['outcome'],'installed_full_hash_verified')
        self.assertTrue(saved['restore_started']);self.assertTrue(saved['partition_may_be_modified'])
        self.assertEqual(dev.writes,['candidate']);self.assertEqual(h.entries,0)
        self.assertEqual(json.loads((host.directory/'0001-result.json').read_text())['status'],'uncertain')
        RECORDS.append(dict(probe='FIXED_decode_inverse',escaped=None,partition_may_be_modified_present=True,nested_result_receipt_exists=True,install_outcome=saved['install_result']['outcome'],dispatches=len(calls)))

    def test_decode_error_after_install_stops_without_inverse(self):
        """A direct helper decoder exception crosses the previous CLI boundary."""
        real=M.MemoryTransport.safety_snapshot;host=T.HostIO(self.root/'nested');calls=[]
        def process(argv,**kw):
            calls.append(argv)
            if len(calls)==12:return b'\xff'.decode('utf-8')
            return answer(argv,kw.get('input'))
        def snapshot(t,*args):
            if t.phase=='entry-guard':
                with patch.object(T,'subprocess',types.SimpleNamespace(run=process,TimeoutExpired=subprocess.TimeoutExpired)):
                    transport=T.Transport(self.root,t.journal,'install',M.RUN,'entry-guard',M.OLD,host)
                    transport.authorization_check=lambda:None
                    transport.root('FIXTURE_ONLY','decode_probe')
            return real(t,*args)
        with patch.object(M.MemoryTransport,'safety_snapshot',snapshot):dev,h,r=self.trial()
        self.assertEqual(len(calls),12);self.assertEqual(dev.writes,['candidate'])
        self.assertEqual(r['outcome'],'transport_uncertain_no_retry');self.assertTrue(r['partition_may_be_modified'])
        self.assertEqual(h.entries,0)
        self.assertEqual(json.loads((host.directory/'0012-result.json').read_text())['status'],'uncertain')
        RECORDS.append(dict(probe='FIXED_decode_after_install',dispatches=len(calls),writes=dev.writes,outcome=r['outcome'],entry_requests=h.entries,nested_result_receipt_exists=True))

    def test_completed_operation_failure_still_reaches_frozen_status(self):
        host=T.HostIO(self.root/'nested')
        def process(argv,**kw):
            p=answer(argv,kw.get('input'))
            if kw.get('input'):
                p.stdout=re.sub(r'(ASUS_RECOVERY_RC_[0-9a-f]{32}=)0',r'\g<1>7',p.stdout)
            return p
        with patch.object(T,'subprocess',types.SimpleNamespace(run=process,TimeoutExpired=subprocess.TimeoutExpired)):
            p=helper(host)
        self.assertEqual(p.returncode,0);self.assertEqual(E.root_status(p,'a'*32),7)
        RECORDS.append(dict(probe='completed_failure',helper_status=p.returncode,operation_status=7))

    def test_query_stderr_is_retained_in_aggregate_and_nested_journal(self):
        host=T.HostIO(self.root/'nested');calls=[]
        def process(argv,**kw):
            calls.append(argv);return answer(argv,kw.get('input'),'QUERY_WARNING\n' if len(calls)==1 else '')
        with patch.object(T,'subprocess',types.SimpleNamespace(run=process,TimeoutExpired=subprocess.TimeoutExpired)):
            result=helper(host)
        self.assertEqual(result.stderr,'QUERY_WARNING\n')
        self.assertEqual(json.loads((host.directory/'0001-result.json').read_text())['stderr'],'QUERY_WARNING\n')
        RECORDS.append(dict(probe='STREAM_difference',nested_query_stderr='QUERY_WARNING\n',aggregate_helper_stderr=result.stderr,retained_in_nested_journal=True))

with (R/'evidence/adversarial-r2.txt').open('w') as stream:
    result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Review))
receipt=dict(tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),harness_passed=result.wasSuccessful(),regression_assertions_require_safe_outcomes=True,device_contacted=False,records=RECORDS)
(R/'evidence/adversarial-r2.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({k:v for k,v in receipt.items() if k!='records'}))
raise SystemExit(not result.wasSuccessful())
