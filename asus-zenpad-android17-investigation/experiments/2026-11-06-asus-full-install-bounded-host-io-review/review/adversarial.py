"""Independent offline production-flow review; never launches a real transport.

The unchanged baseline module supplies ONLY tiny fake-image/peer helpers.
Correctness assertions deliberately fail on the reviewed revision's defects.
Policy/contract/transport marker inputs for new parent trials exist in memory.
"""
import contextlib
import io
import json
import os
from pathlib import Path
import resource
import signal
import sys
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
import test_bounded as base
from test_bounded import (budgets, sha, chunks, source_client, parent_remote,
                          sources, client, DeadlineExpired, PoisonedSession,
                          PipeSession, Phase, reap_owned)

OBSERVATIONS = []
REAL_OPEN = Path.open
REAL_READ_BYTES = Path.read_bytes
REAL_FSYNC = os.fsync
REAL_WRITE = os.write


class Review(base.Tests):
    # Loader below selects only review_* methods, never duplicates baselines.
    def setUp(self):
        self.fd_before = len(os.listdir('/dev/fd'))
        super().setUp()
        self.note = {}
        self.fd = None
        self.s = None
        self.book = None
        self.parent_calls = []

    def spawn(self,kind,config):
        if kind!='readback':return super().spawn(kind,config)
        self.ordinal+=1
        path=self.root/f'peer-{self.ordinal}.json';path.write_text(json.dumps(config))
        p=base.REAL_POPEN([sys.executable,'-B',str(ROOT/'review/readback_peer.py'),kind,str(path)],
            stdin=base.subprocess.PIPE,stdout=base.subprocess.PIPE,stderr=base.subprocess.PIPE,bufsize=0)
        self.children.append(p);base.CHILDREN.append(p)
        base.MAX_LIVE_CHILDREN=max(base.MAX_LIVE_CHILDREN,sum(p.poll() is None for p in base.CHILDREN))
        return p

    def tearDown(self):
        name = self._testMethodName
        dest = ROOT / 'evidence/adversarial' / name
        dest.mkdir(parents=True, exist_ok=True)
        for p in self.root.iterdir():
            if p.name.endswith('.log') or p.name in ('journal', 'parent-evidence', 'parent-evidence.stderr'):
                (dest / p.name).write_bytes(p.read_bytes())
        self.note.update(case=name, target_ops=self.ops(),
                         source_ops=[e['source_op'] for e in self.events('source') if 'source_op' in e],
                         parent_calls=self.parent_calls,
                         session=None if self.fd is None else dict(dead=self.fd.dead, closed=self.fd.closed,
                             outcome=self.fd.outcome, possible_partition_modification=self.fd.possible_partition_modification),
                         children_created=len(self.children))
        super().tearDown()
        self.note.update(all_children_reaped=all(p.returncode is not None for p in self.children),
                         all_child_streams_closed=all(f is None or f.closed for p in self.children for f in (p.stdin,p.stdout,p.stderr)),
                         fd_before=self.fd_before, fd_after=len(os.listdir('/dev/fd')))
        OBSERVATIONS.append(self.note)
        (dest/'observation.json').write_text(json.dumps(self.note,indent=2)+'\n')
        self.assertEqual(self.note['fd_after'], self.note['fd_before'])

    def setup_flow(self, **limits):
        self.book = budgets(**limits)
        self.s = self.source(self.book)
        self.prepared = source_client.prepare_source(self.m,0,self.s,sha(self.data).hex())
        self.fd = self.target(self.book)

    def write(self, journal=None, inverse=None):
        with (self.root/'journal').open('w') as raw:
            source_client.write_image(self.fd,self.m,b'P'*32,0,self.s,sha(self.data).hex(),
                journal(raw) if journal else raw,prepared=self.prepared,budgets=self.book,inverse_from=inverse)

    def expire(self, phase):
        # Finite deterministic injected guard latency; no clock replacement.
        time.sleep(max(0,phase.deadline-time.monotonic())+.025)
        self.note['expired_phase'] = phase.name
        self.note['deadline_reached'] = time.monotonic() >= phase.deadline

    def review_reconciliation_fsync_expiry(self):
        self.setup_flow(reconciliation=[.15,.15])
        def fsync(n):
            REAL_FSYNC(n)
            if self.fd.phase.name == 'reconciliation': self.expire(self.fd.phase)
        error = None
        with patch('os.fsync',side_effect=fsync):
            try:self.write()
            except BaseException as e:error=type(e).__name__
        self.note['error']=error
        self.assertNotIn(3,self.ops(), 'BEGIN sent after reconciliation journal fsync exhausted phase')

    def review_control_journal_expiry(self):
        self.setup_flow()
        self.fd.set_phase(Phase('control',time.monotonic()+.15,.15))
        outer=self
        class Journal:
            def __init__(self,raw):self.raw=raw;self.once=False
            def __getattr__(self,k):return getattr(self.raw,k)
            def write(self,text):return self.raw.write(text)
            def flush(self):
                self.raw.flush()
                if not self.once:
                    self.once=True;outer.expire(outer.fd.phase)
        self.write(Journal)
        self.assertEqual(self.ops(),[1], 'reconciliation sent after control journal guard expired')

    def review_transfer_final_guard_expiry(self):
        self.setup_flow(transfer=[.2,.2])
        original=self.s.check
        def check():
            original()
            if self.s.next_index == 3:self.expire(self.s.phase)
        with patch.object(self.s,'check',side_effect=check):self.write()
        self.assertNotIn(5,self.ops(), 'whole hash and commit sent after final transfer guard expired')

    def review_receipt_fsync_expiry_direct_api(self):
        self.setup_flow(whole_image_hash=[.2,.2])
        def fsync(n):
            REAL_FSYNC(n)
            if self.fd.phase.name == 'whole_image_hash': self.expire(self.fd.phase)
        with patch('os.fsync',side_effect=fsync):self.write()
        self.assertEqual(self.fd.outcome,'UNKNOWN','success published after whole-image phase expired in receipt fsync')

    def review_receipt_fsync_failure_unknown(self):
        self.setup_flow()
        def fsync(n):
            if self.fd.phase.name == 'whole_image_hash':raise OSError('REVIEW final receipt fsync failed')
            return REAL_FSYNC(n)
        with patch('os.fsync',side_effect=fsync),self.assertRaises(OSError):self.write()
        self.assert_terminal(self.fd)
        journal=(self.root/'journal').read_text()
        self.assertIn('whole_partition_verified',journal)
        self.assertEqual(json.loads(journal.splitlines()[-1])['outcome'],'UNKNOWN')
        self.assertTrue(self.fd.possible_partition_modification)

    def review_receipt_write_failure_unknown(self):
        self.setup_flow()
        class Journal:
            def __init__(self,raw):self.raw=raw
            def __getattr__(self,k):return getattr(self.raw,k)
            def write(self,text):
                if 'whole_partition_verified' in text:raise OSError('REVIEW receipt write failed')
                return self.raw.write(text)
        with self.assertRaises(OSError):self.write(Journal)
        self.assert_terminal(self.fd)

    def review_receipt_short_write_unknown(self):
        self.setup_flow()
        class Journal:
            def __init__(self,raw):self.raw=raw
            def __getattr__(self,k):return getattr(self.raw,k)
            def write(self,text):
                if 'whole_partition_verified' in text:return self.raw.write(text[:8])
                return self.raw.write(text)
        self.write(Journal)
        self.assertEqual(self.fd.outcome,'UNKNOWN','short receipt write fsynced and treated as success')

    def review_source_cleanup_failure_direct_api(self):
        self.setup_flow()
        original=self.s.close
        def close():
            original();raise OSError('REVIEW source cleanup failed after actual reap')
        with patch.object(self.s,'close',side_effect=close),self.assertRaises(OSError):self.write()
        self.note['outcome_immediately_after_cleanup_error']=self.fd.outcome
        late_error=None
        try:self.note['status_after_cleanup_error']=client.status(self.fd)
        except BaseException as e:late_error=type(e).__name__
        self.note['status_after_cleanup_error_exception']=late_error
        self.assertEqual(late_error,'PoisonedSession','further TARGET status accepted after source cleanup failed')
        self.assertEqual(self.fd.outcome,'UNKNOWN','finally error escapes while outcome remains success')

    def review_guard_expiry_mid_chunk_no_more_target(self):
        self.setup_flow(transfer=[.2,.2])
        original=self.s.read_chunk
        def chunk(*args):
            result=original(*args)
            if args[0] == 0:self.expire(self.s.phase)
            return result
        with patch.object(self.s,'read_chunk',side_effect=chunk),self.assertRaises(DeadlineExpired):self.write()
        self.assert_terminal(self.fd);self.assertEqual(self.ops(),[1,2,3])

    def review_same_source_and_target_reuse_refused(self):
        self.setup_flow()
        self.write()
        before=self.ops()
        with self.assertRaises(ValueError):self.write()
        self.assert_terminal(self.fd);self.assertEqual(self.ops(),before)
        with self.assertRaises(ValueError):self.s.open()

    def review_explicit_inverse_success_preserves_opcode_order(self):
        self.setup_flow()
        self.write(inverse=1)
        self.assertEqual(self.ops(),[1,8,3,4,4,4,5,9])
        self.assertEqual(self.fd.outcome,'VERIFIED_COMMIT_RECEIPT')

    def review_parent_manifest_contract_binding_no_child(self):
        self.assertIn('manifest pin',self.parent(contract_override={'manifest_sha256':'0'*64}))
        self.assertEqual(self.children,[])

    def review_source_cannot_move_to_new_phase_after_unobserved_expiry(self):
        self.setup_flow()
        self.s.set_phase(Phase('source-old',time.monotonic()+.04,.04))
        self.expire(self.s.phase)
        error=None
        try:self.s.set_phase(Phase('source-new',time.monotonic()+1,1));self.s.check()
        except BaseException as e:error=type(e).__name__
        self.note['error']=error
        self.assertIsNotNone(error,'expired source resurrected by replacing its phase')

    def parent(self, fault='none', limits=None, bad_pin=None, receipt=False, extra=None, policy_override=None, contract_override=None, operation='write'):
        phases={k:[2,.7] for k in base.Budgets.NAMES}
        phases.update(limits or {})
        policy=dict(phases=phases,host_child_cleanup_seconds=.1)
        policy.update(policy_override or {})
        contract=dict(mode='PARENT_APPROVED',armed=True,manifest_sha256=sha(self.m).hex(),p10_full_sha256=(b'P'*32).hex())
        contract.update(contract_override or {})
        virtual={self.root/'MEMORY-policy':json.dumps(policy).encode(),
                 self.root/'MEMORY-manifest':self.m,
                 self.root/'MEMORY-contract':json.dumps(contract).encode(),
                 self.root/'MEMORY-transport':b'NONEXECUTABLE IN-MEMORY REVIEW MARKER'}
        args=['parent_remote.py',operation,'--execute','--transport-id','999','--image-index','0',
              '--source-profile','stock-system','--image-sha256',sha(self.data).hex(),'--evidence',str(self.root/'parent-evidence')]
        for flag,key in [('io-budgets','policy'),('contract','contract'),('adb','transport')]:
            path=self.root/('MEMORY-'+key)
            args+=['--'+flag,str(path),'--'+flag+'-sha256','0'*64 if bad_pin==key else sha(virtual[path]).hex()]
        args+=['--manifest',str(self.root/'MEMORY-manifest')]
        if operation=='readback':args+=['--part','25','--chunk','0','--output',str(self.root/'readback.log')]
        if receipt:args+=['--source-receipt',str(self.root/'source-receipt.log')]
        def read_bytes(path):return virtual[path] if path in virtual else REAL_READ_BYTES(path)
        def open_path(path,*a,**kw):
            if path in virtual:
                self.assertEqual(a,('rb',));return io.BytesIO(virtual[path])
            return REAL_OPEN(path,*a,**kw)
        def source(key,phase,**kw):
            with patch.object(sources,'reference',return_value=(self.profile,chunks(self.data))):
                self.s=sources.RemoteSource(key,phase,**kw)
            self.s.spawn=lambda:self.spawn('source',dict(profile=self.profile,fault='none',log=str(self.root/'source.log')))
            return self.s
        def transport(command,**kw):
            if operation=='write':self.assertTrue(self.s.verified)
            self.parent_calls.append(command[-1])
            if command[-1]=='features':return self.spawn('features',{})
            self.assertEqual(command[-3:],['shell','-T','rescue-v1'])
            if operation=='readback':return self.spawn('readback',dict(log=str(self.root/'target.log')))
            return self.spawn('target',dict(manifest=self.m.hex(),data=self.data.hex(),fault=fault,skip=False,log=str(self.root/'target.log')))
        def session(*a,**kw):
            self.fd=PipeSession(*a,**kw);return self.fd
        error=None
        with contextlib.ExitStack() as stack:
            for context in (patch.object(sys,'argv',args),patch.object(Path,'read_bytes',read_bytes),patch.object(Path,'open',open_path),
                patch.object(parent_remote,'RemoteSource',side_effect=source),patch.object(parent_remote.subprocess,'Popen',side_effect=transport),
                patch.object(parent_remote,'PipeSession',side_effect=session)):
                stack.enter_context(context)
            if extra:extra(stack)
            try:parent_remote.main()
            except BaseException as e:error=type(e).__name__+': '+str(e)
        self.note['parent_error']=error
        path=self.root/'parent-evidence'
        self.note['parent_journal']=path.read_text() if path.exists() else ''
        return error

    def review_parent_bad_policy_pin_no_child(self):
        self.assertIn('budget policy pin',self.parent(bad_pin='policy'))
        self.assertEqual(self.children,[])

    def review_parent_readback_two_replies_share_message_budget(self):
        error=self.parent(operation='readback',limits={'control':[2,.20]})
        self.assertIsNotNone(error,'two reply frames refresh one request deadline and exceed .20s total')
        self.assertFalse((self.root/'readback.log').exists(),'late readback published as successful')

    def review_parent_bad_contract_pin_no_child(self):
        self.assertIn('contract hash',self.parent(bad_pin='contract'))
        self.assertEqual(self.children,[])

    def review_parent_bad_transport_pin_no_child(self):
        self.assertIn('hash-pinned',self.parent(bad_pin='transport'))
        self.assertEqual(self.children,[])

    def review_parent_invalid_budget_values_no_child(self):
        for value in (True,0,-1,float('nan'),float('inf'),'1',None):
            with self.subTest(value=value):
                error=self.parent(limits={'transfer':[value,1]})
                self.assertIsNotNone(error);self.assertEqual(self.children,[])
        for value in (True,0,-1,float('nan'),float('inf'),'1',None):
            with self.subTest(cleanup=value):
                error=self.parent(policy_override={'host_child_cleanup_seconds':value})
                self.assertIsNotNone(error);self.assertEqual(self.children,[])

    def review_parent_contract_armed_type_refused(self):
        self.parent(contract_override={'armed':'false'})
        self.assertEqual(self.parent_calls,[],'truthy nonboolean armed field reaches production flow')

    def review_parent_partial_transport_write_unknown(self):
        fired=[False]
        def extra(stack):
            original=client.send
            def send(fd,op,b=b''):
                if op==4 and not fired[0]:
                    fired[0]=True
                    calls=[0]
                    def fail_write(n,data):
                        if n==fd.writer:
                            calls[0]+=1
                            if calls[0]>1:raise OSError('REVIEW after partial target request')
                            return REAL_WRITE(n,data[:5])
                        return REAL_WRITE(n,data)
                    with patch('os.write',side_effect=fail_write):return original(fd,op,b)
                return original(fd,op,b)
            stack.enter_context(patch.object(source_client,'send',side_effect=send))
        self.assertIn('OSError',self.parent(extra=extra))
        self.assertTrue(fired[0]);self.assert_terminal(self.fd)
        self.assertEqual(self.ops(),[1,2,3])
        self.assertTrue(self.fd.possible_partition_modification)

    def review_source_reap_failure_retains_ownership(self):
        self.setup_flow()
        proc=self.s.process
        def fail(proc,grace):raise base.subprocess.TimeoutExpired('OWNED-FAKE',grace)
        with patch.object(sources,'reap_owned',side_effect=fail),self.assertRaises(base.subprocess.TimeoutExpired):self.write()
        self.note['source_process_reference_retained']=self.s.process is proc
        self.note['source_child_still_live_before_supervisor_cleanup']=proc.poll() is None
        self.assertIs(self.s.process,proc,'source dropped sole production child reference before successful reap')

    def review_parent_reconciliation_fsync_expiry(self):
        def extra(stack):
            def fsync(n):
                REAL_FSYNC(n)
                if self.fd and self.fd.phase.name=='reconciliation':self.expire(self.fd.phase)
            stack.enter_context(patch('os.fsync',side_effect=fsync))
        self.parent(limits={'reconciliation':[.15,.15]},extra=extra)
        self.assertNotIn(3,self.ops(),'production adapter sent BEGIN after reconciliation expiry')

    def review_parent_preflight_receipt_expiry(self):
        def extra(stack):
            def fsync(n):
                REAL_FSYNC(n)
                if self.s and self.fd is None and self.s.verified:self.expire(self.s.phase)
            stack.enter_context(patch('os.fsync',side_effect=fsync))
        self.parent(limits={'source_preflight':[.2,.2]},receipt=True,extra=extra)
        self.assertEqual(self.parent_calls,[],'features/target opened after preflight receipt guard expired')

    def review_parent_final_fsync_failure_unknown(self):
        calls=[0]
        def extra(stack):
            def fsync(n):
                if self.fd and self.fd.outcome=='VERIFIED_COMMIT_RECEIPT':
                    calls[0]+=1;raise OSError('REVIEW parent final fsync failed')
                return REAL_FSYNC(n)
            stack.enter_context(patch('os.fsync',side_effect=fsync))
        self.assertIsNotNone(self.parent(extra=extra))
        self.assert_terminal(self.fd)
        self.assertIn('whole_partition_verified',self.note['parent_journal'])
        self.assertEqual(json.loads(self.note['parent_journal'].splitlines()[-1])['outcome'],'UNKNOWN')

    def review_parent_final_fsync_expiry(self):
        def extra(stack):
            def fsync(n):
                REAL_FSYNC(n)
                if self.fd and self.fd.outcome=='VERIFIED_COMMIT_RECEIPT':self.expire(self.fd.phase)
            stack.enter_context(patch('os.fsync',side_effect=fsync))
        error=self.parent(limits={'whole_image_hash':[.2,.2]},extra=extra)
        self.assertIsNotNone(error,'parent returned success after final fsync exhausted phase')

    def review_parent_stderr_flush_failure_unknown(self):
        def extra(stack):
            real=Path.open
            class Stream:
                def __init__(self,raw):self.raw=raw
                def __getattr__(self,k):return getattr(self.raw,k)
                def __enter__(self):return self
                def __exit__(self,*a):return self.raw.__exit__(*a)
                def flush(self):self.raw.flush();raise OSError('REVIEW stderr flush failed')
            def opened(path,*a,**kw):
                raw=real(path,*a,**kw)
                return Stream(raw) if path.name=='parent-evidence.stderr' else raw
            stack.enter_context(patch.object(Path,'open',opened))
        self.assertIsNotNone(self.parent(extra=extra))
        self.assertEqual(self.fd.outcome,'UNKNOWN','stderr publication error leaves verified outcome')
        self.assertIn('UNKNOWN',self.note['parent_journal'])

    def review_parent_target_cleanup_failure_unknown(self):
        def extra(stack):
            def reap(proc,grace):
                result=reap_owned(proc,grace)
                if self.fd and proc is self.fd.process and self.parent_calls[-1:] == ['rescue-v1']:
                    raise OSError('REVIEW target cleanup failed after actual reap')
                return result
            stack.enter_context(patch.object(parent_remote,'reap_owned',side_effect=reap))
        self.assertIsNotNone(self.parent(extra=extra))
        self.assertEqual(self.fd.outcome,'UNKNOWN','target cleanup exception leaves verified outcome')
        self.assertIn('UNKNOWN',self.note['parent_journal'])

    def review_parent_lost_commit_no_further_requests(self):
        self.assertIn('DeadlineExpired',self.parent(fault='lost-commit',limits={'whole_image_hash':[.3,.15]}))
        self.assert_terminal(self.fd)
        self.assertEqual(self.ops(),[1,2,3,4,4,4,5,9])
        self.assertNotIn('whole_partition_verified',self.note['parent_journal'])

    def review_parent_mid_source_stall_no_further_requests(self):
        def extra(stack):
            original=base.Tests.spawn
            def spawn(kind,config):
                if kind=='source':config=dict(config,fault='chunk-stall')
                return original(self,kind,config)
            stack.enter_context(patch.object(self,'spawn',side_effect=spawn))
        self.assertIn('DeadlineExpired',self.parent(limits={'transfer':[.3,.15]},extra=extra))
        self.assert_terminal(self.fd);self.assertEqual(self.ops(),[1,2,3,4])


def audit(event,args):
    if event in ('socket.connect','socket.bind','socket.getaddrinfo'):
        raise AssertionError('review prohibits network')
    if event=='subprocess.Popen':
        executable,argv,*_=args
        if executable!=sys.executable or len(argv)!=5 or argv[1]!='-B' or argv[2] not in (str(ROOT/'tests/peers.py'),str(ROOT/'review/readback_peer.py')):
            raise AssertionError('review allows only exact owned fake-peer child: '+repr(argv))


if __name__=='__main__':
    resource.setrlimit(resource.RLIMIT_CPU,(25,25))
    signal.alarm(40)
    memory_error=None
    try:resource.setrlimit(resource.RLIMIT_DATA,(512*1024**2,512*1024**2))
    except (ValueError,OSError) as e:memory_error=repr(e)
    sys.addaudithook(audit)
    suite=unittest.TestSuite(Review(name) for name in sorted(dir(Review)) if name.startswith('review_'))
    start=time.monotonic()
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    own=resource.getrusage(resource.RUSAGE_SELF);child=resource.getrusage(resource.RUSAGE_CHILDREN)
    report=dict(tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),
                failures_detail=[dict(case=str(t),traceback=s) for t,s in result.failures+result.errors],
                wall_seconds=time.monotonic()-start,parent_cpu_seconds=own.ru_utime+own.ru_stime,
                child_cpu_seconds=child.ru_utime+child.ru_stime,parent_maxrss=own.ru_maxrss,child_maxrss=child.ru_maxrss,
                children_created=len(base.CHILDREN),max_live_children=base.MAX_LIVE_CHILDREN,
                all_children_reaped=all(p.returncode is not None for p in base.CHILDREN),
                memory_limit_error=memory_error,observations=OBSERVATIONS)
    (ROOT/'evidence/adversarial-results.json').write_text(json.dumps(report,indent=2)+'\n')
    sys.exit(not result.wasSuccessful())
