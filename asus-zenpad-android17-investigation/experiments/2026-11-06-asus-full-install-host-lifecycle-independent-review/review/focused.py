"""Independent finite fault probes against unchanged production copies.

Only test helpers are reused. These cases assert production state and actual
owned fake-peer opcode logs. All markers for contracts/budgets are in memory.
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
import adversarial as a
from adversarial import base, source_client, parent_remote, sources, client, PipeSession, Phase
from bounded_io import DeadlineExpired, PoisonedSession, UNREAPED_CHILDREN, reap_owned

ROOT=a.ROOT

class Focused(a.Review):
    def terminal(self, modified=True):
        before=self.ops()
        self.assert_terminal(self.fd)
        self.assertEqual(self.fd.possible_partition_modification,modified)
        with self.assertRaises(PoisonedSession):self.fd.set_phase(Phase('no-restart',time.monotonic()+1,1))
        with self.assertRaises(PoisonedSession):self.fd.complete_phase()
        if self.s is not None:
            self.assertTrue(self.s.dead)
            for action in (self.s.open, lambda:self.s.exchange(4), lambda:self.s.read_chunk(0), self.s.receipt):
                with self.assertRaises(ValueError):action()
        self.assertEqual(self.ops(),before)
        self.note['commit_receipt']=self.fd.commit_receipt
        self.note['source_consumed']=None if self.s is None else self.s.consumed

    def last_unknown(self,path):
        text=path.read_text()
        self.note['journal_last_line']=text.splitlines()[-1]
        try:last=json.loads(text.splitlines()[-1])
        except json.JSONDecodeError as error:
            self.fail('durable terminal line is not a complete UNKNOWN JSON record: '+str(error))
        self.assertEqual(last['outcome'],'UNKNOWN')

    def review_direct_partial_success_then_write_error_records_unknown(self):
        self.setup_flow();outer=self
        class Sink:
            def __init__(self,raw):self.raw=raw;self.pending=False;self.failed=False
            def __getattr__(self,k):return getattr(self.raw,k)
            def write(self,text):
                if self.pending:
                    self.pending=False;self.failed=True
                    raise OSError('FOCUSED one-shot error after SUCCESS prefix')
                if not self.failed and '"outcome": "SUCCESS"' in text:
                    self.pending=True
                    return self.raw.write(text[:24])
                return self.raw.write(text)
        with self.assertRaisesRegex(OSError,'one-shot'):self.write(Sink)
        self.terminal();self.assertIsNotNone(self.fd.commit_receipt)
        self.assertEqual(self.ops(),[1,2,3,4,4,4,5,9])
        self.last_unknown(self.root/'journal')

    def review_cli_partial_unknown_then_recovered_sink_records_unknown(self):
        state={'prefix':False,'failed':False,'stderr_failed':False}
        def extra(stack):
            real=Path.open
            class Sink:
                def __init__(self,raw):self.raw=raw
                def __getattr__(self,k):return getattr(self.raw,k)
                def __enter__(self):return self
                def __exit__(self,*args):return self.raw.__exit__(*args)
                def write(self,text):
                    if state['prefix'] and not state['failed']:
                        state['failed']=True
                        raise OSError('FOCUSED one-shot UNKNOWN continuation error')
                    if not state['prefix'] and '"outcome": "UNKNOWN"' in text:
                        state['prefix']=True
                        return self.raw.write(text[:24])
                    return self.raw.write(text)
            class Stderr:
                def __init__(self,raw):self.raw=raw
                def __getattr__(self,k):return getattr(self.raw,k)
                def __enter__(self):return self
                def __exit__(self,*args):return self.raw.__exit__(*args)
                def flush(self):
                    self.raw.flush();state['stderr_failed']=True
                    raise OSError('FOCUSED stderr failed after commit')
            def opened(path,*args,**kwargs):
                raw=real(path,*args,**kwargs)
                if path.name=='parent-evidence' and args==('x',):return Sink(raw)
                if path.name=='parent-evidence.stderr':return Stderr(raw)
                return raw
            stack.enter_context(patch.object(Path,'open',opened))
        self.assertIn('stderr failed after commit',self.parent(extra=extra))
        self.assertTrue(state['failed']);self.assertTrue(state['stderr_failed']);self.terminal()
        self.assertTrue(any(e.get('committed') for e in self.events('target')))
        self.assertIsNotNone(self.fd.commit_receipt)
        self.assertEqual(self.ops(),[1,2,3,4,4,4,5,9])
        self.last_unknown(self.root/'parent-evidence')

    def review_direct_unknown_write_flush_fsync_failures_stay_poisoned(self):
        for fail in ('write','flush','fsync'):
            with self.subTest(fail=fail):
                # A single real flow per sink fault, with separate trace files.
                self.setup_flow();fired=[]
                class Sink:
                    def __init__(self,raw):self.raw=raw;self.unknown=False
                    def __getattr__(self,k):return getattr(self.raw,k)
                    def write(self,text):
                        if 'whole_partition_verified' in text:raise OSError('FOCUSED primary receipt error')
                        if '"outcome": "UNKNOWN"' in text:
                            self.unknown=True
                            if fail=='write':fired.append(True);raise OSError('FOCUSED UNKNOWN write')
                        return self.raw.write(text)
                    def flush(self):
                        if self.unknown and fail=='flush':fired.append(True);raise OSError('FOCUSED UNKNOWN flush')
                        return self.raw.flush()
                def fsync(number):
                    if self.fd.dead and fail=='fsync':fired.append(True);raise OSError('FOCUSED UNKNOWN fsync')
                    return a.REAL_FSYNC(number)
                with patch('os.fsync',side_effect=fsync),self.assertRaisesRegex(OSError,'primary receipt'):self.write(Sink)
                self.terminal();self.assertTrue(fired)
                for name in ('target.log','source.log','journal'):
                    path=self.root/name
                    if path.exists():path.rename(self.root/(fail+'-'+name))

    def review_cli_failure_cleanup_and_unknown_write_failure_stay_poisoned(self):
        fired=[]
        def extra(stack):
            real_open=Path.open
            class Sink:
                def __init__(self,raw):self.raw=raw
                def __getattr__(self,k):return getattr(self.raw,k)
                def __enter__(self):return self
                def __exit__(self,*args):return self.raw.__exit__(*args)
                def write(self,text):
                    if '"outcome": "UNKNOWN"' in text:fired.append('unknown');raise OSError('FOCUSED unusable failure sink')
                    return self.raw.write(text)
            def opened(path,*args,**kwargs):
                raw=real_open(path,*args,**kwargs)
                return Sink(raw) if path.name=='parent-evidence' and args==('x',) else raw
            def reap(proc,grace):
                result=reap_owned(proc,grace)
                if self.fd is not None and proc is self.fd.process and self.parent_calls[-1:]==['rescue-v1']:
                    fired.append('cleanup');raise OSError('FOCUSED cleanup report during lost completion')
                return result
            stack.enter_context(patch.object(Path,'open',opened))
            stack.enter_context(patch.object(parent_remote,'reap_owned',side_effect=reap))
        self.assertIn('cleanup report',self.parent(fault='lost-commit',limits={'whole_image_hash':[.3,.15]},extra=extra))
        self.terminal();self.assertIn('unknown',fired);self.assertIn('cleanup',fired)
        self.assertTrue(any(e.get('committed') for e in self.events('target')))
        self.assertEqual(self.ops(),[1,2,3,4,4,4,5,9])
        self.assertIsNotNone(self.fd.process.returncode)

    def review_cli_deferred_writer_consumed_but_not_success(self):
        states=[]
        def extra(stack):
            real=source_client.write_image
            def writer(*args,**kwargs):
                result=real(*args,**kwargs)
                states.append((self.fd.outcome,self.s.consumed,self.s.process))
                self.assertFalse(kwargs['finalize'])
                self.assertEqual(self.fd.outcome,'COMMIT_RECEIVED')
                self.assertTrue(self.s.consumed);self.assertIsNone(self.s.process)
                raise OSError('FOCUSED after intermediate commit before parent exit')
            stack.enter_context(patch.object(source_client,'write_image',side_effect=writer))
        self.assertIn('after intermediate',self.parent(extra=extra));self.assertEqual(len(states),1)
        self.terminal();self.assertNotIn('"outcome": "SUCCESS"',self.note['parent_journal'])
        self.last_unknown(self.root/'parent-evidence')

    def review_direct_consumed_source_on_fresh_target_refused_before_request(self):
        self.setup_flow();self.write();first=self.fd
        newbook=base.budgets();self.fd=self.target(newbook)
        before=self.ops()
        with self.assertRaisesRegex(ValueError,'consumed'):
            with (self.root/'journal-2.log').open('w') as raw:
                source_client.write_image(self.fd,self.m,b'P'*32,0,self.s,base.sha(self.data).hex(),raw,prepared=self.prepared,budgets=newbook)
        self.terminal(False);self.assertEqual(self.ops(),before)
        self.assertEqual(first.outcome,'VERIFIED_COMMIT_RECEIPT')

    def review_complete_phase_with_pending_request_poisoned(self):
        self.setup_flow();client.send(self.fd,1)
        with self.assertRaises(PoisonedSession):self.fd.complete_phase()
        # It is legal to close the owned source host session; never send cleanup.
        self.s.close();self.terminal(False)

    def review_cli_source_receipt_close_error_no_target(self):
        def extra(stack):
            real=Path.open
            class Sink:
                def __init__(self,raw):self.raw=raw
                def __getattr__(self,k):return getattr(self.raw,k)
                def __enter__(self):return self
                def __exit__(self,*args):self.raw.__exit__(*args);raise OSError('FOCUSED SOURCE receipt close')
            def opened(path,*args,**kwargs):
                raw=real(path,*args,**kwargs)
                return Sink(raw) if path.name=='source-receipt.log' else raw
            stack.enter_context(patch.object(Path,'open',opened))
        self.assertIn('SOURCE receipt close',self.parent(receipt=True,extra=extra))
        self.assertEqual(self.parent_calls,[]);self.assertIsNone(self.fd)
        self.assertTrue(self.s.dead);self.assertIsNone(self.s.process)
        self.assertEqual(self.ops(),[])

    def review_cli_all_nonboolean_armed_values_refused(self):
        for value in (False,'false','true',1,0,None,[],{},[1]):
            with self.subTest(value=value):
                self.assertIn('armed session',self.parent(contract_override={'armed':value}))
                self.assertEqual(self.children,[]);self.assertEqual(self.parent_calls,[])
        self.assertIsNone(self.parent(contract_override={'armed':True}))
        self.assertEqual(self.fd.outcome,'VERIFIED_COMMIT_RECEIPT')

    def stderr_fault(self,operation):
        def extra(stack):
            real=Path.open
            class Sink:
                def __init__(self,raw):self.raw=raw
                def __getattr__(self,k):return getattr(self.raw,k)
                def __enter__(self):return self
                def __exit__(self,*args):return self.raw.__exit__(*args)
                def flush(self):self.raw.flush();raise OSError('FOCUSED final stderr publication')
            def opened(path,*args,**kwargs):
                raw=real(path,*args,**kwargs)
                return Sink(raw) if path.name=='parent-evidence.stderr' else raw
            stack.enter_context(patch.object(Path,'open',opened))
        self.assertIn('stderr publication',self.parent(operation=operation,extra=extra))
        self.terminal(False);self.last_unknown(self.root/'parent-evidence')
        self.assertNotIn('"outcome": "SUCCESS"',self.note['parent_journal'])

    def review_cli_status_final_stderr_failure_unknown(self):self.stderr_fault('status')
    def review_cli_reconcile_final_stderr_failure_unknown(self):self.stderr_fault('reconcile')
    def review_cli_readback_final_stderr_failure_unknown(self):self.stderr_fault('readback')

    def review_cli_readback_short_output_is_completed(self):
        def extra(stack):
            real=Path.open
            class Sink:
                def __init__(self,raw):self.raw=raw
                def __getattr__(self,k):return getattr(self.raw,k)
                def __enter__(self):return self
                def __exit__(self,*args):return self.raw.__exit__(*args)
                def write(self,data):return self.raw.write(data[:2])
            def opened(path,*args,**kwargs):
                raw=real(path,*args,**kwargs)
                return Sink(raw) if path.name=='readback.log' and args==('xb',) else raw
            stack.enter_context(patch.object(Path,'open',opened))
        self.assertIsNone(self.parent(operation='readback',extra=extra))
        self.assertEqual((self.root/'readback.log').read_bytes(),b'owned fake readback')
        self.assertEqual(self.fd.outcome,'SUCCESS');self.assertEqual(self.ops(),[6])

    def review_direct_source_stream_close_error_still_reaps_and_poison(self):
        self.setup_flow();proc=self.s.process;real=proc.stdin
        class Stream:
            @property
            def closed(self):return real.closed
            def close(self):real.close();raise OSError('FOCUSED source stdin close reported error')
        proc.stdin=Stream()
        try:
            with self.assertRaisesRegex(OSError,'source stdin close'):self.write()
            self.assertIsNotNone(proc.returncode);self.assertIs(self.s.process,proc)
            self.assertNotIn(proc.pid,UNREAPED_CHILDREN)
            self.terminal();self.assertIsNotNone(self.fd.commit_receipt)
        finally:proc.stdin=real;self.s.close()

if __name__=='__main__':
    resource.setrlimit(resource.RLIMIT_CPU,(30,30));signal.alarm(55)
    memory_error=None
    try:resource.setrlimit(resource.RLIMIT_DATA,(512*1024**2,512*1024**2))
    except (ValueError,OSError) as error:memory_error=repr(error)
    sys.addaudithook(a.audit)
    suite=unittest.TestSuite(Focused(name) for name in sorted(dir(Focused)) if name.startswith('review_') and name in Focused.__dict__)
    start=time.monotonic();result=unittest.TextTestRunner(verbosity=2).run(suite)
    own=resource.getrusage(resource.RUSAGE_SELF);child=resource.getrusage(resource.RUSAGE_CHILDREN)
    report=dict(tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),
        failures_detail=[dict(case=str(t),traceback=trace) for t,trace in result.failures+result.errors],
        wall_seconds=time.monotonic()-start,parent_cpu_seconds=own.ru_utime+own.ru_stime,child_cpu_seconds=child.ru_utime+child.ru_stime,
        parent_maxrss=own.ru_maxrss,child_maxrss=child.ru_maxrss,children_created=len(base.CHILDREN),max_live_children=base.MAX_LIVE_CHILDREN,
        all_children_reaped=all(p.returncode is not None for p in base.CHILDREN),
        all_child_streams_closed=all(f is None or f.closed for p in base.CHILDREN for f in (p.stdin,p.stdout,p.stderr)),
        unreaped_registry_count=len(UNREAPED_CHILDREN),memory_limit_error=memory_error,observations=a.OBSERVATIONS)
    (ROOT/'evidence/focused-results.json').write_text(json.dumps(report,indent=2)+'\n')
    sys.exit(not result.wasSuccessful())
