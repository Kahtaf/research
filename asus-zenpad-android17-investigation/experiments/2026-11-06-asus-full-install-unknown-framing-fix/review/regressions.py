"""Re-run actual review injections with corrected terminal expectations.

The original adversarial.py remains byte-exact beside this file. Changes here
accept DeadlineExpired where the old review expected a silently bad return,
and accept a fully completed short write as the permitted repair.
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

import adversarial as original
from adversarial import base, source_client, parent_remote, sources, client, DeadlineExpired, PipeSession, Phase
from journal import BoundedJournal, write_all
from bounded_io import UNREAPED_CHILDREN
ROOT=original.ROOT


class Regression(original.Review):
    def terminal_unknown(self):
        self.assert_terminal(self.fd)
        if self.fd.possible_partition_modification:
            self.assertTrue(self.fd.possible_partition_modification)
        self.assertEqual(self.fd.outcome,'UNKNOWN')

    def review_control_journal_expiry(self):
        with self.assertRaises(DeadlineExpired):super().review_control_journal_expiry()
        self.terminal_unknown();self.assertEqual(self.ops(),[1])

    def review_transfer_final_guard_expiry(self):
        with self.assertRaises(DeadlineExpired):super().review_transfer_final_guard_expiry()
        self.terminal_unknown();self.assertEqual(self.ops(),[1,2,3,4,4,4])

    def review_receipt_fsync_expiry_direct_api(self):
        with self.assertRaises(DeadlineExpired):super().review_receipt_fsync_expiry_direct_api()
        self.terminal_unknown()
        self.assertEqual(json.loads((self.root/'journal').read_text().splitlines()[-1])['outcome'],'UNKNOWN')

    def review_receipt_short_write_unknown(self):
        self.setup_flow()
        class Journal:
            def __init__(self,raw):self.raw=raw
            def __getattr__(self,key):return getattr(self.raw,key)
            def write(self,text):
                if 'whole_partition_verified' in text:return self.raw.write(text[:8])
                return self.raw.write(text)
        self.write(Journal)
        rows=[json.loads(line) for line in (self.root/'journal').read_text().splitlines() if line]
        self.assertTrue(any(r.get('intermediate') and r.get('whole_partition_verified') for r in rows))
        self.assertEqual(rows[-1]['outcome'],'SUCCESS')
        self.assertEqual(self.fd.outcome,'VERIFIED_COMMIT_RECEIPT')

    def final_publication_fault(self, *, expire=False):
        real=source_client.publish_success
        fired=[]
        def extra(stack):
            def publish(fd,evidence):
                self.assertIsNone(self.s.process)
                self.assertIsNotNone(fd.process.returncode)
                def fsync(number):
                    original.REAL_FSYNC(number)
                    fired.append(True)
                    if expire:self.expire(fd.phase)
                    else:raise OSError('REGRESSION final parent fsync failed')
                with patch('os.fsync',side_effect=fsync):return real(fd,evidence)
            stack.enter_context(patch.object(source_client,'publish_success',side_effect=publish))
        error=self.parent(limits={'whole_image_hash':[.3,.3]},extra=extra)
        self.assertTrue(fired);self.assertIsNotNone(error)
        self.terminal_unknown()
        self.assertEqual(json.loads(self.note['parent_journal'].splitlines()[-1])['outcome'],'UNKNOWN')
        self.assertEqual(self.ops(),[1,2,3,4,4,4,5,9])

    def review_parent_final_fsync_failure_unknown(self):self.final_publication_fault()
    def review_parent_final_fsync_expiry(self):self.final_publication_fault(expire=True)

    def review_completed_preflight_can_idle_during_control(self):
        def extra(stack):
            real=parent_remote.features_owned
            def features(*args):
                self.assertTrue(self.s.io.phase_completed)
                self.expire(self.s.phase)
                return real(*args)
            stack.enter_context(patch.object(parent_remote,'features_owned',side_effect=features))
        self.assertIsNone(self.parent(limits={'source_preflight':[.2,.2]},extra=extra))
        self.assertEqual(self.fd.outcome,'VERIFIED_COMMIT_RECEIPT')
        self.assertEqual(json.loads(self.note['parent_journal'].splitlines()[-1])['outcome'],'SUCCESS')

    def review_completed_control_source_can_idle_during_reconciliation(self):
        self.setup_flow(reconciliation=[1,.8])
        original_reconcile=source_client.reconcile
        def reconcile(*args):
            self.assertTrue(self.s.io.phase_completed)
            self.expire(self.s.phase)
            return original_reconcile(*args)
        # The source's control phase is shorter than reconciliation; the target
        # has legitimately moved on, while the completed source phase is idle.
        self.fd.set_phase(Phase('control',time.monotonic()+.15,.15))
        with patch.object(source_client,'reconcile',side_effect=reconcile):self.write()
        self.assertEqual(self.fd.outcome,'VERIFIED_COMMIT_RECEIPT')

    def review_new_io_reactivates_completed_phase(self):
        self.setup_flow()
        self.fd.set_phase(Phase('control-active',time.monotonic()+.15,.15))
        self.fd.complete_phase()
        self.assertEqual(client.status(self.fd),'fake idle')
        self.assertFalse(self.fd.phase_completed)
        self.expire(self.fd.phase)
        with self.assertRaises(DeadlineExpired):self.fd.set_phase(Phase('new',time.monotonic()+1,1))
        self.terminal_unknown();self.assertEqual(self.ops(),[1])

    def review_parent_readback_positive_one_budget(self):
        self.assertIsNone(self.parent(operation='readback',limits={'control':[2,.5]}))
        self.assertEqual((self.root/'readback.log').read_bytes(),b'owned fake readback')
        self.assertEqual(self.ops(),[6])
        self.assertEqual(self.fd.outcome,'SUCCESS')

    def review_direct_source_cleanup_guard_expiry(self):
        self.setup_flow(whole_image_hash=[.25,.25])
        close=self.s.close
        def delayed():close();self.expire(self.fd.phase)
        with patch.object(self.s,'close',side_effect=delayed),self.assertRaises(DeadlineExpired):self.write()
        self.terminal_unknown()
        rows=[json.loads(line) for line in (self.root/'journal').read_text().splitlines() if line]
        self.assertNotIn('SUCCESS',[r.get('outcome') for r in rows])
        self.assertIsNotNone(self.fd.commit_receipt)

    def review_parent_cleanup_guard_expiry(self):
        def extra(stack):
            def reap(proc,grace):
                result=base.reap_owned(proc,grace)
                if self.fd and proc is self.fd.process and self.parent_calls[-1:]==['rescue-v1']:self.expire(self.fd.phase)
                return result
            stack.enter_context(patch.object(parent_remote,'reap_owned',side_effect=reap))
        self.assertIn('DeadlineExpired',self.parent(limits={'whole_image_hash':[.25,.25]},extra=extra))
        self.terminal_unknown();self.assertNotIn('SUCCESS',self.note['parent_journal'])

    def review_parent_stderr_close_failure_unknown(self):
        def extra(stack):
            real=Path.open
            class Stream:
                def __init__(self,raw):self.raw=raw
                def __getattr__(self,key):return getattr(self.raw,key)
                def __enter__(self):return self
                def __exit__(self,*args):self.raw.__exit__(*args);raise OSError('REGRESSION stderr context close')
            def opened(path,*args,**kwargs):
                raw=real(path,*args,**kwargs)
                return Stream(raw) if path.name=='parent-evidence.stderr' else raw
            stack.enter_context(patch.object(Path,'open',opened))
        self.assertIsNotNone(self.parent(extra=extra))
        self.terminal_unknown();self.assertNotIn('SUCCESS',self.note['parent_journal'])
        self.assertEqual(json.loads(self.note['parent_journal'].splitlines()[-1])['outcome'],'UNKNOWN')

    def review_parent_evidence_close_failure_poison_even_broken_sink(self):
        def extra(stack):
            real=Path.open
            class Stream:
                def __init__(self,raw):self.raw=raw
                def __getattr__(self,key):return getattr(self.raw,key)
                def __enter__(self):return self
                def __exit__(self,*args):self.raw.__exit__(*args);raise OSError('REGRESSION journal context close')
            def opened(path,*args,**kwargs):
                raw=real(path,*args,**kwargs)
                return Stream(raw) if path.name=='parent-evidence' and args==('x',) else raw
            stack.enter_context(patch.object(Path,'open',opened))
        self.assertIsNotNone(self.parent(extra=extra))
        self.terminal_unknown()
        self.assertTrue(any(e.get('committed') for e in self.events('target')))
        self.assertEqual(json.loads(self.note['parent_journal'].splitlines()[-1])['outcome'],'UNKNOWN')

    def review_parent_journal_close_expiry_records_unknown(self):
        def extra(stack):
            real=Path.open;outer=self
            class Stream:
                def __init__(self,raw):self.raw=raw
                def __getattr__(self,key):return getattr(self.raw,key)
                def __enter__(self):return self
                def __exit__(self,*args):
                    result=self.raw.__exit__(*args);outer.expire(outer.fd.phase);return result
            def opened(path,*args,**kwargs):
                raw=real(path,*args,**kwargs)
                return Stream(raw) if path.name=='parent-evidence' and args==('x',) else raw
            stack.enter_context(patch.object(Path,'open',opened))
        self.assertIn('DeadlineExpired',self.parent(limits={'whole_image_hash':[.25,.25]},extra=extra))
        self.terminal_unknown()
        self.assertEqual(json.loads(self.note['parent_journal'].splitlines()[-1])['outcome'],'UNKNOWN')

    def review_closed_journal_replacement_is_never_appended(self):
        marker=b'OWNED REPLACEMENT; MUST STAY UNCHANGED'
        def extra(stack):
            real=Path.open;outer=self
            class Stream:
                def __init__(self,raw,path):self.raw,self.path=raw,path
                def __getattr__(self,key):return getattr(self.raw,key)
                def __enter__(self):return self
                def __exit__(self,*args):
                    self.raw.__exit__(*args)
                    self.path.rename(outer.root/'original-owned-journal')
                    self.path.write_bytes(marker)
                    raise OSError('REGRESSION replaced owned evidence path after close')
            def opened(path,*args,**kwargs):
                raw=real(path,*args,**kwargs)
                return Stream(raw,path) if path.name=='parent-evidence' and args==('x',) else raw
            stack.enter_context(patch.object(Path,'open',opened))
        self.assertIsNotNone(self.parent(extra=extra));self.terminal_unknown()
        self.assertEqual((self.root/'parent-evidence').read_bytes(),marker)
        self.assertEqual(self.ops(),[1,2,3,4,4,4,5,9])

    def review_parent_stderr_short_write_completed(self):
        def extra(stack):
            real=Path.open
            class Stream:
                def __init__(self,raw):self.raw=raw
                def __getattr__(self,key):return getattr(self.raw,key)
                def __enter__(self):return self
                def __exit__(self,*args):return self.raw.__exit__(*args)
                def write(self,data):return self.raw.write(data[:1024])
            def opened(path,*args,**kwargs):
                raw=real(path,*args,**kwargs)
                return Stream(raw) if path.name=='parent-evidence.stderr' else raw
            stack.enter_context(patch.object(Path,'open',opened))
        self.assertIsNone(self.parent(fault='stderr',extra=extra))
        self.assertEqual(len((self.root/'parent-evidence.stderr').read_bytes()),65536)
        self.assertEqual(self.fd.outcome,'VERIFIED_COMMIT_RECEIPT')

    def review_zero_none_invalid_receipt_write_unknown(self):
        for value in (0,None,-1,True,10**6):
            with self.subTest(value=value):
                self.setup_flow()
                class Journal:
                    def __init__(self,raw):self.raw=raw
                    def __getattr__(self,key):return getattr(self.raw,key)
                    def write(self,text):
                        if 'whole_partition_verified' in text:return value
                        return self.raw.write(text)
                with self.assertRaises(OSError):self.write(Journal)
                self.terminal_unknown();self.assertIsNotNone(self.fd.commit_receipt)
                self.assertEqual(json.loads((self.root/'journal').read_text().splitlines()[-1])['outcome'],'UNKNOWN')

    def review_bounded_journal_short_sink_writes_complete(self):
        class Short(io.StringIO):
            def write(self,text):return super().write(text[:3])
        sink=Short();journal=BoundedJournal(sink,1024)
        text=json.dumps({'receipt':'complete'})+'\n'
        self.assertEqual(journal.write(text),len(text));self.assertEqual(sink.getvalue(),text)
        with self.assertRaises(ValueError):BoundedJournal(sink,1).write(text)

    def review_source_receipt_short_write_completed_before_target(self):
        def extra(stack):
            real=Path.open
            class Stream:
                def __init__(self,raw):self.raw=raw
                def __getattr__(self,key):return getattr(self.raw,key)
                def __enter__(self):return self
                def __exit__(self,*args):return self.raw.__exit__(*args)
                def write(self,text):return self.raw.write(text[:7])
            def opened(path,*args,**kwargs):
                raw=real(path,*args,**kwargs)
                return Stream(raw) if path.name=='source-receipt.log' else raw
            stack.enter_context(patch.object(Path,'open',opened))
        self.assertIsNone(self.parent(receipt=True,extra=extra))
        receipt=json.loads((self.root/'source-receipt.log').read_text())
        self.assertTrue(receipt['full_preflight']);self.assertFalse(receipt['target_authorized'])

    def review_wrong_boundary_schema_types_before_children(self):
        for value in ('12',{'x':1},None,True,[],[1], [1,2,3]):
            with self.subTest(pair=value):
                self.assertIsNotNone(self.parent(limits={'transfer':value}));self.assertEqual(self.children,[])
        for field in ('mode','manifest_sha256','p10_full_sha256'):
            for value in (None,True,12,{},[]):
                with self.subTest(field=field,value=value):
                    self.assertIsNotNone(self.parent(contract_override={field:value}));self.assertEqual(self.children,[])

    def review_reap_wait_failure_keeps_registry_and_source_reference(self):
        self.setup_flow()
        proc=self.s.process
        real_wait=proc.wait
        def fail(*args,**kwargs):raise base.subprocess.TimeoutExpired('OWNED-FAKE',.01)
        with patch.object(proc,'wait',side_effect=fail),self.assertRaises(base.subprocess.TimeoutExpired):self.s.close()
        self.assertIs(self.s.process,proc);self.assertIs(UNREAPED_CHILDREN[proc.pid],proc)
        proc.wait=real_wait
        self.s.close()
        self.assertIsNone(self.s.process);self.assertNotIn(proc.pid,UNREAPED_CHILDREN)


if __name__=='__main__':
    resource.setrlimit(resource.RLIMIT_CPU,(30,30));signal.alarm(55)
    memory_error=None
    try:resource.setrlimit(resource.RLIMIT_DATA,(512*1024**2,512*1024**2))
    except (ValueError,OSError) as e:memory_error=repr(e)
    sys.addaudithook(original.audit)
    start=time.monotonic()
    suite=unittest.TestSuite(Regression(name) for name in sorted(dir(Regression)) if name.startswith('review_'))
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    own=resource.getrusage(resource.RUSAGE_SELF);child=resource.getrusage(resource.RUSAGE_CHILDREN)
    report=dict(tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),
                failures_detail=[dict(case=str(t),traceback=trace) for t,trace in result.failures+result.errors],
                wall_seconds=time.monotonic()-start,parent_cpu_seconds=own.ru_utime+own.ru_stime,
                child_cpu_seconds=child.ru_utime+child.ru_stime,parent_maxrss=own.ru_maxrss,child_maxrss=child.ru_maxrss,
                children_created=len(base.CHILDREN),max_live_children=base.MAX_LIVE_CHILDREN,
                all_children_reaped=all(p.returncode is not None for p in base.CHILDREN),
                unreaped_registry_count=len(UNREAPED_CHILDREN),memory_limit_error=memory_error,
                observations=original.OBSERVATIONS)
    (ROOT/'evidence/regression-results.json').write_text(json.dumps(report,indent=2)+'\n')
    sys.exit(not result.wasSuccessful())
