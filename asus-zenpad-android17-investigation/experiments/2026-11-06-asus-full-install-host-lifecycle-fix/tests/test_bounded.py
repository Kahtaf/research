import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import resource
import select
import socket
import struct
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'source'))
import bounded_client as client
from bounded_io import Budgets,Phase,PipeSession,DeadlineExpired,PoisonedSession,reap_owned
import parent_remote
import source_client
import sources
import worker
from pinned import client as legacy

REAL_POPEN=subprocess.Popen
CHILDREN=[]
MAX_LIVE_CHILDREN=0
C=worker.CHUNK


def sha(data):return hashlib.sha256(data).digest()
def chunks(data):return b''.join(sha(data[i:i+C]) for i in range(0,len(data),C))
def manifest(data):
    result=b'ASUSR002'+struct.pack('<II',2,2)+b'I'*96
    for i,b in enumerate((data,b'fake-boot')):
        result+=struct.pack('<IIQ',i,9 if i else 25,len(b))+sha(b)+struct.pack('<I',len(chunks(b))//32)+chunks(b)
    return result


def budgets(**overrides):
    # QA ONLY tiny-fixture times. No hardware timing policy is supplied.
    limits={k:[3.,1.] for k in Budgets.NAMES}
    limits.update(overrides)
    return Budgets(limits)


class Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=ROOT/'evidence',prefix='qa-owned-')
        self.root=Path(self.temp.name)
        self.children=[]
        self.sessions=[]
        self.sockets=[]
        self.data=b'A'*C+b'Z'*C+b'Q'*3584
        self.raw=self.root/'fake.raw';self.raw.write_bytes(self.data);self.raw.chmod(0o400)
        self.profile=dict(role=0,path=str(self.raw),size=len(self.data),sha256=sha(self.data).hex(),
                          uid=os.getuid(),gid=os.getgid(),mode=0o400,nlink=1,chunk_bytes=C,
                          count=3,chunks_sha256=sha(chunks(self.data)).hex())
        self.m=manifest(self.data)
        self.ordinal=0

    def tearDown(self):
        for s in self.sessions:s.close()
        for s in self.sockets:s.close()
        for p in self.children:
            reap_owned(p,.15)
            self.assertIsNotNone(p.returncode)
            self.assertTrue(all(f is None or f.closed for f in (p.stdin,p.stdout,p.stderr)))
        self.temp.cleanup()

    def spawn(self,kind,config):
        self.ordinal+=1
        path=self.root/f'peer-{self.ordinal}.json';path.write_text(json.dumps(config))
        p=REAL_POPEN([sys.executable,'-B',str(ROOT/'tests/peers.py'),kind,str(path)],
                     stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,bufsize=0)
        self.children.append(p);CHILDREN.append(p)
        global MAX_LIVE_CHILDREN
        MAX_LIVE_CHILDREN=max(MAX_LIVE_CHILDREN,sum(p.poll() is None for p in CHILDREN))
        return p

    def source(self,book,fault='none'):
        log=self.root/'source.log'
        with patch.object(sources,'reference',return_value=(self.profile,chunks(self.data))):
            s=sources.RemoteSource('stock-system',book.start('source_preflight'),cleanup_seconds=.15)
        s.spawn=lambda:self.spawn('source',{'profile':self.profile,'fault':fault,'log':str(log)})
        return s.open()

    def target(self,book,fault='none',skip=False):
        p=self.spawn('target',{'manifest':self.m.hex(),'data':self.data.hex(),'fault':fault,
                               'skip':skip,'log':str(self.root/'target.log')})
        fd=PipeSession(p.stdout.fileno(),p.stdin.fileno(),book.start('control'),
                       stderr=p.stderr.fileno(),process=p)
        self.sessions.append(fd)
        return fd

    def events(self,name):
        p=self.root/(name+'.log')
        return [json.loads(x) for x in p.read_text().splitlines()] if p.exists() else []

    def ops(self):return [e['target_op'] for e in self.events('target') if 'target_op' in e]

    def flow(self,*,source_fault='none',target_fault='none',skip=False,book=None,stop=None):
        book=book or budgets()
        s=self.source(book,source_fault)
        prepared=source_client.prepare_source(self.m,0,s,sha(self.data).hex(),stop)
        fd=self.target(book,target_fault,skip)
        self.last_source,self.last_fd=s,fd
        with (self.root/'journal').open('w') as evidence:
            source_client.write_image(fd,self.m,b'P'*32,0,s,sha(self.data).hex(),evidence,
                                      stop_after=stop,prepared=prepared,budgets=book)
        return fd

    def raw_session(self,action,seconds=.12,**extra):
        p=self.spawn('raw',dict(action=action,**extra))
        # READY is exactly one owned-child write; finite external readiness wait.
        self.assertTrue(select.select([p.stdout],[],[],1)[0])
        self.assertEqual(os.read(p.stdout.fileno(),5),b'READY')
        fd=PipeSession(p.stdout.fileno(),p.stdin.fileno(),
                       Phase('qa',time.monotonic()+seconds,seconds),stderr=p.stderr.fileno(),process=p)
        self.sessions.append(fd)
        return fd

    def assert_terminal(self,fd):
        self.assertTrue(fd.dead);self.assertEqual(fd.outcome,'UNKNOWN')
        for op in (1,2,3,4,5,7,8,9):
            with self.assertRaises(PoisonedSession):client.send(fd,op)
        with self.assertRaises(PoisonedSession):client.receive(fd,0x84)

    def test_target_partial_header(self):
        fd=self.raw_session('partial-header');t=time.monotonic()
        with self.assertRaises(DeadlineExpired):client.receive(fd,0x84)
        self.assertLess(time.monotonic()-t,.5);self.assert_terminal(fd)

    def test_target_partial_body(self):
        fd=self.raw_session('partial-body')
        with self.assertRaises(DeadlineExpired):client.receive(fd,0x84)
        self.assert_terminal(fd)

    def test_target_read_empty_pipe(self):
        fd=self.raw_session('silent')
        with self.assertRaises(DeadlineExpired):client.receive(fd,0x84)
        self.assert_terminal(fd)

    def test_target_write_full_pipe(self):
        fd=self.raw_session('silent')
        with self.assertRaises(DeadlineExpired):client.send(fd,4,b'X'*C)
        self.assertTrue(fd.possible_partition_modification);self.assert_terminal(fd)

    def test_near_deadline_writability(self):
        fd=self.raw_session('near',seconds=.35,delay=.20)
        client.send(fd,4,b'X'*C)
        self.assertFalse(fd.dead)
        fd.close()

    def test_slow_drip_header_and_body_do_not_extend_message(self):
        fd=self.raw_session('drip',seconds=.18);t=time.monotonic()
        with self.assertRaises(DeadlineExpired):client.receive(fd,0x84)
        self.assertLess(time.monotonic()-t,.4);self.assert_terminal(fd)

    def test_child_exit_eof(self):
        fd=self.raw_session('exit')
        with self.assertRaises(EOFError):client.receive(fd,0x84)
        self.assert_terminal(fd)

    def test_stderr_backpressure_drained_with_bounded_retention(self):
        fd=self.raw_session('stderr',seconds=1)
        self.assertEqual(client.receive(fd,0x84),struct.pack('<II',0,0))
        self.assertEqual(len(fd.stderr_tail),65536)

    def test_trailing_stderr_and_exit_drained_finitely(self):
        fd=self.raw_session('tail-stderr',seconds=1)
        self.assertEqual(client.receive(fd,0x84),struct.pack('<II',0,0))
        self.assertEqual(fd.read_stream_end(0),b'')
        self.assertEqual(len(fd.stderr_tail),65536)

    def test_plain_feature_output_size_and_stall_are_bounded(self):
        fd=self.raw_session('silent')
        with self.assertRaises(DeadlineExpired):fd.read_stream_end(4096)
        self.assert_terminal(fd)
        fd=self.raw_session('stderr',seconds=1)
        with self.assertRaises(ValueError):fd.read_stream_end(2)
        self.assert_terminal(fd)

    def test_eintr_eagain_and_partial_writes_actual_flow(self):
        real_write,real_read=os.write,os.read
        calls={'w':0,'r':0}
        def write(fd,data):
            calls['w']+=1
            if calls['w']==1:raise InterruptedError()
            if calls['w']==2:raise BlockingIOError()
            return real_write(fd,data[:4096])
        def read(fd,n):
            calls['r']+=1
            if calls['r']==1:raise InterruptedError()
            if calls['r']==2:raise BlockingIOError()
            return real_read(fd,min(n,8192))
        book=budgets();s=self.source(book)
        prepared=source_client.prepare_source(self.m,0,s,sha(self.data).hex())
        fd=self.target(book)
        with patch('bounded_io.os.write',side_effect=write),patch('bounded_io.os.read',side_effect=read):
            with (self.root/'journal').open('w') as e:
                source_client.write_image(fd,self.m,b'P'*32,0,s,sha(self.data).hex(),e,prepared=prepared,budgets=book)
        self.assertEqual(fd.outcome,'VERIFIED_COMMIT_RECEIPT');self.assertGreater(calls['w'],500)

    def test_full_multichunk_positive(self):
        fd=self.flow()
        self.assertEqual(fd.outcome,'VERIFIED_COMMIT_RECEIPT')
        self.assertEqual(self.ops(),[1,2,3,4,4,4,5,9])
        self.assertEqual(len([e for e in self.events('source') if 'held_fd' in e]),1)
        self.assertTrue(any(e.get('tail_preserved') for e in self.events('target')))

    def test_skip_positive_and_tail_preserved(self):
        fd=self.flow(skip=True)
        self.assertEqual(self.ops(),[1,2,3,7,4,4,5,9])
        self.assertEqual(fd.outcome,'VERIFIED_COMMIT_RECEIPT')
        self.assertTrue(any(e.get('tail_preserved') for e in self.events('target')))

    def test_both_source_and_target_stderr_in_actual_flow(self):
        fd=self.flow(source_fault='stderr',target_fault='stderr')
        self.assertEqual(fd.outcome,'VERIFIED_COMMIT_RECEIPT')
        self.assertEqual(len(fd.stderr_tail),65536)
        self.assertEqual(len(self.last_source.io.stderr_tail),65536)

    def test_partial_ack_actual_flow(self):
        with self.assertRaises(DeadlineExpired):self.flow(target_fault='partial-ack',book=budgets(transfer=[1,.15]))
        fd=self.last_fd;self.assert_terminal(fd)
        self.assertEqual(self.ops(),[1,2,3,4]);self.assertTrue(fd.possible_partition_modification)

    def test_partial_ack_header_actual_flow(self):
        with self.assertRaises(DeadlineExpired):self.flow(target_fault='ack-header',book=budgets(transfer=[1,.15]))
        self.assert_terminal(self.last_fd);self.assertEqual(self.ops(),[1,2,3,4])

    def test_ack_slowdrip_actual_flow(self):
        with self.assertRaises(DeadlineExpired):self.flow(target_fault='ack-drip',book=budgets(transfer=[1,.16]))
        self.assert_terminal(self.last_fd);self.assertEqual(self.ops(),[1,2,3,4])

    def test_lost_final_commit_unknown_even_when_target_committed(self):
        with self.assertRaises(DeadlineExpired):self.flow(target_fault='lost-commit',book=budgets(whole_image_hash=[1,.15]))
        self.assert_terminal(self.last_fd)
        self.assertTrue(any(e.get('committed') for e in self.events('target')))
        text=(self.root/'journal').read_text()
        self.assertIn('UNKNOWN',text);self.assertNotIn('whole_partition_verified',text)
        self.assertEqual(self.ops(),[1,2,3,4,4,4,5,9])

    def test_final_commit_child_exit_unknown(self):
        with self.assertRaises(EOFError):self.flow(target_fault='commit-exit')
        self.assert_terminal(self.last_fd)
        self.assertTrue(any(e.get('committed') for e in self.events('target')))

    def test_mid_source_stall_poisons_target_no_more_requests(self):
        with self.assertRaises(DeadlineExpired):self.flow(source_fault='chunk-stall',book=budgets(transfer=[1,.15]))
        self.assert_terminal(self.last_fd);self.assertTrue(self.last_source.dead)
        self.assertEqual(self.ops(),[1,2,3,4])
        self.assertTrue(any(e.get('accepted_chunk')==0 for e in self.events('target')))
        self.assertTrue(self.last_fd.possible_partition_modification)
        for action in (self.last_source.open,lambda:self.last_source.exchange(4)):
            with self.assertRaises(ValueError):action()

    def test_source_write_full_pipe_at_actual_exchange(self):
        s=self.source(budgets(source_preflight=[1,.14]),'no-read')
        # Fill only the owned fake child's pipe, after its valid hello.
        while True:
            try:os.write(s.process.stdin.fileno(),b'X'*4096)
            except BlockingIOError:break
        with self.assertRaises(DeadlineExpired):s.preflight()
        self.assertTrue(s.dead);self.assertTrue(s.io.dead)
        for action in (s.open,s.preflight,lambda:s.exchange(4)):
            with self.assertRaises(ValueError):action()
        self.assertEqual(self.ops(),[])

    def test_source_identity_and_chunk_table_guards(self):
        for fault in ('hello-profile','hello-stat','bad-chunks'):
            with self.subTest(fault=fault):
                with self.assertRaises(ValueError):
                    s=self.source(budgets(),fault)
                    source_client.prepare_source(self.m,0,s,sha(self.data).hex())
                self.assertEqual(self.ops(),[])

    def test_live_source_digest_guard_before_target_chunk(self):
        with self.assertRaises(ValueError):self.flow(source_fault='bad-chunk-digest')
        self.assert_terminal(self.last_fd);self.assertEqual(self.ops(),[1,2,3])

    def test_held_fd_type_path_mode_owner_and_link_guards(self):
        for field,value in (('size',len(self.data)+1),('mode',0o600),('uid',os.getuid()+1),('nlink',2)):
            with self.subTest(field=field):
                with self.assertRaises(ValueError):worker.HeldRaw(dict(self.profile,**{field:value}))
        link=self.root/'symlink';link.symlink_to(self.raw)
        with self.assertRaises(ValueError):worker.HeldRaw(dict(self.profile,path=str(link)))
        fifo=self.root/'fifo';os.mkfifo(fifo,0o400)
        with self.assertRaises(ValueError):worker.HeldRaw(dict(self.profile,path=str(fifo)))
        hard=self.root/'hard';os.link(self.raw,hard)
        with self.assertRaises(ValueError):worker.HeldRaw(self.profile)

    def test_target_binding_drift_refused_before_begin(self):
        book=budgets();s=self.source(book)
        prepared=source_client.prepare_source(self.m,0,s,sha(self.data).hex());fd=self.target(book)
        with (self.root/'journal').open('w') as e:
            with self.assertRaises(EOFError):source_client.write_image(fd,self.m,b'X'*32,0,s,sha(self.data).hex(),e,prepared=prepared,budgets=book)
        self.assert_terminal(fd);self.assertEqual(self.ops(),[1,2])
        self.assertFalse(fd.possible_partition_modification)

    def test_source_hello_partial_header(self):
        with self.assertRaises(DeadlineExpired):self.source(budgets(source_preflight=[.25,.15]),'hello-header')
        self.assertEqual(self.ops(),[])

    def test_source_slowdrip_preflight(self):
        s=self.source(budgets(source_preflight=[1,.15]),'source-drip')
        with self.assertRaises(DeadlineExpired):source_client.prepare_source(self.m,0,s,sha(self.data).hex())
        self.assertTrue(s.dead);self.assertEqual(self.ops(),[])

    def test_distinct_reconciliation_phase_budget(self):
        with self.assertRaises(DeadlineExpired):self.flow(target_fault='reconcile-stall',book=budgets(reconciliation=[.14,2.]))
        self.assert_terminal(self.last_fd);self.assertEqual(self.ops(),[1,2])
        self.assertFalse(self.last_fd.possible_partition_modification)

    def test_distinct_wholeimagehash_phase_budget(self):
        with self.assertRaises(DeadlineExpired):self.flow(target_fault='whole-stall',book=budgets(whole_image_hash=[.14,2.]))
        self.assert_terminal(self.last_fd);self.assertEqual(self.ops(),[1,2,3,4,4,4,5])

    def test_phase_deadline_not_extended_by_successful_messages(self):
        fd=self.raw_session('near',seconds=.08,delay=0)
        client.send(fd,4,b'X'*1024)
        time.sleep(.09)
        # A fresh message allowance cannot resurrect the expired phase.
        with self.assertRaises(DeadlineExpired):client.receive(fd,0x84)
        self.assert_terminal(fd)

    def test_expiry_after_guard_source_no_target_send(self):
        book=budgets();s=self.source(book)
        prepared=source_client.prepare_source(self.m,0,s,sha(self.data).hex());fd=self.target(book)
        phase=Phase('control',time.monotonic()+.06,.06);fd.set_phase(phase)
        real=s.check
        def delayed():
            real();time.sleep(.08)
        with patch.object(s,'check',side_effect=delayed):
            with (self.root/'journal').open('w') as e:
                with self.assertRaises(DeadlineExpired):source_client.write_image(fd,self.m,b'P'*32,0,s,sha(self.data).hex(),e,prepared=prepared,budgets=book)
        self.assert_terminal(fd);self.assertEqual(self.ops(),[])

    def test_expiry_at_os_boundary_after_readiness(self):
        fd=self.raw_session('stderr',seconds=.06)
        original=fd._wait
        def delayed(*args):original(*args);time.sleep(.08)
        with patch.object(fd,'_wait',side_effect=delayed),patch('bounded_io.os.write',side_effect=AssertionError('late write')):
            with self.assertRaises(DeadlineExpired):client.send(fd,4,b'X')
        self.assert_terminal(fd)

    def test_prepared_source_binding_refusal(self):
        book=budgets();s=self.source(book);prepared=source_client.prepare_source(self.m,0,s,sha(self.data).hex())
        fd=self.target(book)
        with (self.root/'journal').open('w') as e:
            with self.assertRaisesRegex(ValueError,'prepared source/selection'):
                source_client.write_image(fd,self.m,b'P'*32,0,s,'0'*64,e,prepared=prepared,budgets=book)
        self.assertEqual(self.ops(),[]);self.assert_terminal(fd)

    def test_source_mutation_before_target_is_refused(self):
        book=budgets();s=self.source(book,'mutation')
        with self.assertRaises((EOFError,ValueError)):source_client.prepare_source(self.m,0,s,sha(self.data).hex())
        self.assertTrue(s.dead);self.assertEqual(self.ops(),[])

    def test_source_mid_mutation_no_next_target_chunk(self):
        with self.assertRaises((EOFError,ValueError)):self.flow(source_fault='mid-mutation')
        self.assert_terminal(self.last_fd);self.assertEqual(self.ops(),[1,2,3,4])

    def test_target_wrong_ack_or_whole_poison(self):
        for fault in ('wrong-ack','wrong-whole'):
            with self.subTest(fault=fault):
                with self.assertRaises(ValueError):self.flow(target_fault=fault)
                self.assert_terminal(self.last_fd)
                self.assertNotIn(9,self.ops())
                (self.root/'target.log').unlink()

    def test_explicit_partial_trial_poison_no_commit(self):
        self.flow(stop=1)
        self.assert_terminal(self.last_fd);self.assertEqual(self.ops(),[1,2,3,4])
        self.assertTrue(self.last_source.consumed)

    def test_budget_validation_and_no_restart(self):
        for x in (0,-1,float('inf'),float('nan'),True):
            with self.assertRaises(ValueError):budgets(transfer=[x,1])
        with self.assertRaises(ValueError):Budgets({})
        b=budgets();b.start('source_preflight')
        with self.assertRaises(ValueError):b.start('source_preflight')

    def test_unknown_profiles_and_paths_remain_unbound(self):
        phase=Phase('test',time.monotonic()+1,1)
        with patch.object(sources.subprocess,'Popen',side_effect=AssertionError('launch forbidden')):
            for key in ('install-system','install-boot','../../etc/passwd'):
                with self.assertRaisesRegex(ValueError,'UNBOUND_REFUSED'):sources.RemoteSource(key,phase,cleanup_seconds=.1)
            with self.assertRaises(ValueError):sources.local_source(self.raw,phase,cleanup_seconds=.1)

    def test_original_parse_and_inverse_guard_unchanged(self):
        self.assertEqual(client.parse(self.m),legacy.parse(self.m))
        fd=self.raw_session('silent')
        with self.assertRaisesRegex(ValueError,'explicit original inverse'):client.reconcile(fd,self.m,b'P'*32,0,inverse_from=2)
        self.assertIsNone(fd.pending)

    def test_parent_plan_only_and_explicit_budget_required(self):
        with patch.object(sys,'argv',['parent_remote.py','write']),contextlib.redirect_stdout(io.StringIO()) as out,patch.object(parent_remote.subprocess,'Popen',side_effect=AssertionError('launch forbidden')):
            parent_remote.main()
        self.assertIn('PLAN_ONLY',out.getvalue())
        with patch.object(sys,'argv',['parent_remote.py','write','--execute']):
            with self.assertRaisesRegex(ValueError,'budgets required'):parent_remote.main()

    def test_parent_actual_adapter_full_flow_and_unknown_commit(self):
        for fault in ('none','lost-commit'):
            with self.subTest(fault=fault):
                def put(name,data):
                    path=self.root/name;path.write_bytes(data);return path,sha(data).hex()
                m,msha=put('fake-m',self.m)
                ct,csha=put('fake-c',json.dumps(dict(mode='PARENT_APPROVED',armed=True,manifest_sha256=msha,p10_full_sha256=(b'P'*32).hex())).encode())
                adb,asha=put('NEVER-EXECUTABLE',b'QA ONLY NOT A PROGRAM')
                policy,psha=put('fake-budget',json.dumps(dict(phases={k:[3,.3 if k!='whole_image_hash' else .15] for k in Budgets.NAMES},host_child_cleanup_seconds=.15)).encode())
                evidence=self.root/('parent-'+fault)
                args=['parent_remote.py','write','--execute','--io-budgets',str(policy),'--io-budgets-sha256',psha,
                      '--adb',str(adb),'--adb-sha256',asha,'--transport-id','999','--contract',str(ct),
                      '--contract-sha256',csha,'--manifest',str(m),'--image-index','0','--source-profile','stock-system',
                      '--image-sha256',sha(self.data).hex(),'--evidence',str(evidence)]
                created=[];calls=[]
                def source(key,phase,**kw):
                    with patch.object(sources,'reference',return_value=(self.profile,chunks(self.data))):s=sources.RemoteSource(key,phase,**kw)
                    s.spawn=lambda:self.spawn('source',dict(profile=self.profile,fault='none',log=str(self.root/'source.log')))
                    created.append(s);return s
                def transport(command,**kw):
                    self.assertTrue(created[0].verified)
                    calls.append(command[-1])
                    if command[-1]=='features':return self.spawn('features',{})
                    self.assertEqual(command[-3:],['shell','-T','rescue-v1'])
                    return self.spawn('target',dict(manifest=self.m.hex(),data=self.data.hex(),fault=fault,skip=True,log=str(self.root/'target.log')))
                with patch.object(sys,'argv',args),patch.object(parent_remote,'RemoteSource',side_effect=source),patch.object(parent_remote.subprocess,'Popen',side_effect=transport):
                    if fault=='none':parent_remote.main()
                    else:
                        with self.assertRaises(DeadlineExpired):parent_remote.main()
                self.assertEqual(calls,['features','rescue-v1'])
                self.assertEqual(self.ops(),[1,2,3,7,4,4,5,9])
                self.assertTrue(any(e.get('committed') for e in self.events('target')))
                text=evidence.read_text()
                if fault=='none':self.assertIn('whole_partition_verified',text)
                else:
                    self.assertIn('UNKNOWN',text);self.assertNotIn('whole_partition_verified',text)
                    self.assertIn('"possible_partition_modification": true',text)
                (self.root/'target.log').unlink()

    def test_expired_features_budget_prevents_process_work(self):
        phase=Phase('control',time.monotonic()-.1,1)
        with patch.object(parent_remote.subprocess,'Popen',side_effect=AssertionError('late process')):
            with self.assertRaises(DeadlineExpired):parent_remote.features_owned(['QA-ONLY'],phase,.1)

    def test_parent_preflight_stall_zero_features_or_target_calls(self):
        self.parent_preflight_gate('preflight-stall',False)

    def test_parent_preflight_success_precedes_features(self):
        self.parent_preflight_gate('none',True)

    def parent_preflight_gate(self,fault,success):
        # Ephemeral fake schema data references only tiny owned fixtures. Deleted
        # by tearDown; fake ADB bytes are nonexecutable and never launched.
        def put(name,data):
            path=self.root/name;path.write_bytes(data);return path,sha(data).hex()
        m,msha=put('fake-manifest',self.m)
        contract,csha=put('fake-contract',json.dumps(dict(mode='PARENT_APPROVED',armed=True,manifest_sha256=msha,p10_full_sha256=(b'P'*32).hex())).encode())
        adb,asha=put('NEVER-EXECUTABLE',b'QA ONLY NOT A PROGRAM')
        policy,psha=put('QA-ONLY-budgets',json.dumps(dict(phases={k:[1,.15] for k in Budgets.NAMES},host_child_cleanup_seconds=.15)).encode())
        args=['parent_remote.py','write','--execute','--io-budgets',str(policy),'--io-budgets-sha256',psha,
              '--adb',str(adb),'--adb-sha256',asha,'--transport-id','999','--contract',str(contract),
              '--contract-sha256',csha,'--manifest',str(m),'--image-index','0','--source-profile','stock-system',
              '--image-sha256',sha(self.data).hex(),'--evidence',str(self.root/'parent.log')]
        created=[];features=[]
        def source(key,phase,**kw):
            with patch.object(sources,'reference',return_value=(self.profile,chunks(self.data))):s=sources.RemoteSource(key,phase,**kw)
            s.spawn=lambda:self.spawn('source',dict(profile=self.profile,fault=fault,log=str(self.root/'source.log')))
            created.append(s);return s
        def feature(*a,**kw):
            self.assertTrue(created[0].verified);features.append(a)
            return ['no-shell-v2']
        with patch.object(sys,'argv',args),patch.object(parent_remote,'RemoteSource',side_effect=source),patch.object(parent_remote,'features_owned',side_effect=feature),patch.object(parent_remote.subprocess,'Popen',side_effect=AssertionError('TARGET launch forbidden')):
            with self.assertRaises(ValueError if success else DeadlineExpired):parent_remote.main()
        self.assertEqual(len(features),int(success));self.assertEqual(self.ops(),[])
        self.assertTrue(created[0].dead)

    def test_legacy_actual_hangs_retained_with_own_supervisor(self):
        for kind in ('legacy-read','legacy-write'):
            p=self.spawn(kind,{})
            self.assertTrue(select.select([p.stdout],[],[],1)[0]);self.assertEqual(os.read(p.stdout.fileno(),5),b'READY')
            if kind=='legacy-read':os.write(p.stdin.fileno(),b'RSC1'+struct.pack('<II',0x84,8)+b'123')
            t=time.monotonic()
            with self.assertRaises(subprocess.TimeoutExpired):p.wait(timeout=.15)
            self.assertIsNone(p.poll())
            # Do not drain legacy-write's full output pipe.
            p.terminate();p.wait(timeout=.5)
            self.assertLess(time.monotonic()-t,.7)


class Result(unittest.TextTestResult):
    rows=[]
    def startTest(self,test):self.start=time.monotonic();super().startTest(test)
    def stopTest(self,test):
        self.rows.append(dict(test=str(test),seconds=round(time.monotonic()-self.start,4)))
        super().stopTest(test)


if __name__=='__main__':
    resource.setrlimit(resource.RLIMIT_CPU,(35,35))
    memory_limit_error=None
    try:resource.setrlimit(resource.RLIMIT_DATA,(512*1024**2,512*1024**2))
    except (ValueError,OSError) as e:memory_limit_error=repr(e)
    start=time.monotonic()
    result=unittest.TextTestRunner(verbosity=2,resultclass=Result).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    usage=resource.getrusage(resource.RUSAGE_SELF);child=resource.getrusage(resource.RUSAGE_CHILDREN)
    report=dict(passed=result.wasSuccessful(),tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),
                wall_seconds=round(time.monotonic()-start,3),parent_cpu_seconds=usage.ru_utime+usage.ru_stime,
                children_cpu_seconds=child.ru_utime+child.ru_stime,parent_maxrss=usage.ru_maxrss,children_maxrss=child.ru_maxrss,
                rss_units='bytes on Darwin; KiB on Linux',children_created=len(CHILDREN),max_live_children=MAX_LIVE_CHILDREN,all_children_reaped=all(p.returncode is not None for p in CHILDREN),
                child_cpu_limit_seconds=5,child_wall_limit_seconds=5,parent_cpu_limit_seconds=35,memory_limit_error=memory_limit_error,
                memory_policy='1 GiB workload ceiling; Darwin hard memory/affinity not enforced',
                test_cases=Result.rows)
    (ROOT/'evidence/qa.json').write_text(json.dumps(report,indent=2)+'\n')
    sys.exit(not result.wasSuccessful())
