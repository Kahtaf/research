import dataclasses
import importlib.util
import json
import os
from pathlib import Path
import resource
import socket
import struct
import subprocess
import sys
import time
import threading
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'source'))
import transport as t

# Bound each sequential local test process. No parallel workers or build invocation.
resource.setrlimit(resource.RLIMIT_CPU,(60,60))
try:resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
except (ValueError,OSError):pass
if hasattr(os,'sched_setaffinity'):os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
BASE=ROOT/'evidence'/('tests-'+str(time.time_ns()))
BASE.mkdir()
RUN='11111111-1111-4111-8111-111111111111'
NONCE='a'*64


def fixture_install(d, deploy):
    """Regular files only, independently shaped input to the actual reviewed verifier."""
    install=d/'deploy-runs'/RUN/'install';install.mkdir(parents=True)
    b=deploy.b
    pin=dict(schema=2,run_id=RUN,profile=deploy.PROFILE,code_sha256=t.DEPLOY_SHA,
             candidate_sha256=t.IMAGE,full_p10_sha256=t.P10,created_at=time.time()-1000,
             created_monotonic=time.monotonic()-1000,host_clock_epoch=deploy.host_clock_epoch(),
             stock=dict(serial=b.SERIAL,state='device',usb='1-3.2',product='WW_P00A',model='P00A',device='P00A_2',transport_id='3'),
             properties=deploy.PROPS,enforcing=True,boot_id='22222222-2222-4222-8222-222222222222')
    state=dict(mode='EXECUTE',run_id=RUN,profile=deploy.PROFILE,code_sha256=t.DEPLOY_SHA,
               profile_sha256=deploy.PROFILE_SHA,candidate_sha256=t.IMAGE,full_p10_sha256=t.P10,
               outcome='installed_full_hash_verified',cleanup='verified',partition_status='exact_candidate',
               live_completion_token_sha256=t.sha(NONCE.encode()),pin=pin,started_at=1,completed_at=time.time()-500,
               write_dispatches=[dict(source='candidate',command='write.json')],captures=[])
    (install/'write.json').write_text(json.dumps({'at':3}))
    stock=t.read(b.BACKUPS[0]);full=t.read(t.BUILD/'artifacts/candidate/UNAPPROVED-STOCK-ONLY.img')
    full+=bytes(b.SIZE-len(full))
    for n,data,at in [('before',stock,2),('after',full,4)]:
        session='/fixture/only'; token='b'*32
        root=dict(argv=['adb','-s',b.ENDPOINT,'shell','timeout 60 /data/local/tmp/asus-mtk-su64 -c /system/bin/sh'],
                  stdin=b.DEVICE_GUARD+'\n'+f'dd if={b.BLOCK} of={session}/vault/readback.bin bs=512 count={b.SECTORS}\n'+
                  f'ASUS_RECOVERY_RC_{token}=')
        completion=dict(status='returned',exit_status=0,stdout=f'ASUS_RECOVERY_RC_{token}=0\n',stderr='')
        capture=dict(source=b.BLOCK,run_id=RUN,pin_sha256=deploy.object_sha(pin),bytes=b.SIZE,
                     sha256=t.sha(data),at=at,file=n+'.bin',session=session)
        (install/capture['file']).write_bytes(data)
        pull=dict(argv=['adb','-s',b.ENDPOINT,'pull',session+'/inbox/readback.bin',str(install/capture['file'])])
        for key,value in [('root_intent',root),('root_completion',completion),('pull_intent',pull),
                          ('pull_completion',dict(status='returned',exit_status=0))]:
            name=n+'-'+key+'.json';raw=json.dumps(value).encode();(install/name).write_bytes(raw)
            capture[key]=dict(file=name,sha256=t.sha(raw))
        state['captures'].append(capture)
    raw=json.dumps(state).encode();(install/'state.json').write_bytes(raw)
    deploy.RUNS=d/'deploy-runs'
    return t.sha(raw),state


class Cases(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.measure,cls.deployment=t.load_reviewed()
        cls.popen=subprocess.Popen

    def setUp(self):
        self.d=BASE/self.id().split('.')[-1];self.d.mkdir()
        self.config=self.d/'config.json';self.config.write_text('{"mode":"ok"}')
        self.lock=self.d/'lock';self.lock.touch()
        self.source_sha=t.LOADED_SOURCE_SHA
        self.install_sha,self.install=fixture_install(self.d,self.deployment)
        self.binding=t.Commissioning(RUN,'33333333-3333-4333-8333-333333333333','OFFLINE FIXTURE ONLY','c'*64,
                                      self.install_sha,'1-3.2',17,time.time(),time.monotonic(),self.deployment.host_clock_epoch())
        self.children=[]
        def fake_popen(argv,**kwargs):
            self.assertEqual(argv[0],str(t.ADB),'No executable other than fixed ADB may be requested')
            proc=self.popen([sys.executable,'-B',str(ROOT/'tests/fake_shell.py'),str(self.config),*argv[1:]],**kwargs)
            self.children.append(proc)
            return proc
        self.patches=[patch.object(t,'RUNS',self.d/'runs'),patch.object(t,'LOCK',self.lock),
                      patch.object(t,'load_reviewed',return_value=(self.measure,self.deployment)),
                      patch.object(subprocess,'Popen',side_effect=fake_popen),
                      patch.object(t,'server_version',return_value=None)]
        for p in self.patches:p.start();self.addCleanup(p.stop)

    def tearDown(self):
        for p in self.children:
            self.assertIsNotNone(p.poll(),'Leaked local child')

    def mode(self,value):self.config.write_text(json.dumps({'mode':value}))
    def calls(self):
        path=self.d/'calls.jsonl'
        return [json.loads(s)['argv'] for s in path.read_text().splitlines()] if path.exists() else []
    def events(self):
        path=self.d/'runs'/self.binding.rescue_session_id/'events.jsonl'
        return [json.loads(s) for s in path.read_text().splitlines()]
    def observe(self,**kwargs):
        return t.observe(self.binding,NONCE,expected_source_sha256=self.source_sha,seconds=10,**kwargs)
    def unknown(self,mode):
        self.mode(mode)
        with self.assertRaises(t.Refused):self.observe()
        self.assertEqual(self.events()[-1]['result'],'UNKNOWN')
        calls=self.calls();self.assertEqual(sum('shell' in a for a in calls),1)
        self.assertEqual(calls[-1][-2:],['devices','-l']) # last dispatch is send-boundary inventory
        self.assertEqual((self.d/'request.bin').read_bytes(),self.measure.REQUEST)
        self.assertNotIn(b'EPHEMERAL_TEST_TOKEN',b''.join(p.read_bytes() for p in (self.d/'runs').rglob('*.jsonl')))

    def test_default_cli_is_plan_only(self):
        # Bypass the test Popen substitution only for this owned CLI process.
        with patch.object(subprocess,'Popen',self.popen):
            proc=subprocess.run([sys.executable,'-B',str(ROOT/'source/transport.py')],capture_output=True,timeout=5)
        self.assertEqual(proc.returncode,0);self.assertEqual(json.loads(proc.stdout)['mode'],'PLAN_ONLY')
        self.assertFalse(self.calls())

    def test_fragmented_success_exact_request_eof_and_durable_terminal(self):
        self.mode('fragment');result=self.observe()
        self.assertEqual(result,self.events()[-1]);self.assertEqual(result['adb_exit_status'],0)
        self.assertEqual(result['source_derived_partition_read_bytes'],3804123136)
        self.assertEqual((self.d/'request.bin').read_bytes(),self.measure.REQUEST)
        self.assertTrue(json.loads((self.d/'host-eof.json').read_text())['eof'])
        self.assertEqual(sum('shell' in a for a in self.calls()),1)
        self.assertEqual(self.calls()[3][-5:],['shell','-T','-e','none','rescue-v1'])
        self.assertEqual(os.stat(Path(result['terminal_evidence'])).st_mode & 0o777,0o600)

    def test_premature_eof(self):self.unknown('eof')
    def test_malformed_header(self):self.unknown('bad_header')
    def test_bad_bitmap(self):self.unknown('bad_bitmap')
    def test_remote_nonzero_after_match_is_unknown(self):
        self.unknown('remote_nonzero')
        self.assertEqual(self.events()[-1]['adb_exit_status'],19)
    def test_extra_stdout_is_unknown(self):self.unknown('trailer')

    def test_stderr_flood_bounded_and_no_token_persistence(self):
        self.mode('stderr');result=self.observe()
        self.assertGreater(result['stderr_bytes_discarded'],1_000_000)
        self.assertNotIn('EPHEMERAL_TEST_TOKEN',(self.d/'runs'/self.binding.rescue_session_id/'events.jsonl').read_text())

    def test_consumed_session_refuses_before_commands(self):
        self.observe();count=len(self.calls())
        with self.assertRaises(FileExistsError):self.observe()
        self.assertEqual(len(self.calls()),count)

    def test_wrong_and_stale_usb_stop_before_request(self):
        for mode in ('wrong_usb','stale_usb'):
            with self.subTest(mode=mode):
                self.mode(mode)
                self.binding=dataclasses.replace(self.binding,rescue_session_id=str(__import__('uuid').uuid4()))
                with self.assertRaises(t.Refused):self.observe()
                self.assertEqual(self.events()[-1]['result'],'UNKNOWN')
                self.assertFalse((self.d/'request.bin').exists())
        self.assertEqual(sum('shell' in a for a in self.calls()),0)

    def test_bad_bindings_before_children(self):
        original=self.binding
        for change in (dict(created_monotonic=time.monotonic()-181),dict(created_wall=time.time()-181),
                       dict(created_wall=time.time()+30),dict(host_clock_epoch='other'),dict(transport_id=0),
                       dict(full_p10_sha256='0'*64),dict(manifest_sha256='0'*64),dict(image_sha256='0'*64),
                       dict(usb_vid='0000'),dict(install_state_sha256='0'*64),dict(run_id=str(__import__('uuid').uuid4()))):
            self.binding=dataclasses.replace(original,**change)
            with self.subTest(change=change),self.assertRaises(Exception):self.observe()
        self.assertFalse(self.calls())

    def test_live_install_nonce_required_not_visible_hash(self):
        for token in (None,'0'*64,t.sha(NONCE.encode())):
            with self.assertRaises(Exception):t.observe(self.binding,token,expected_source_sha256=self.source_sha)
        self.assertFalse(self.calls())

    def test_consumed_install_or_changed_capture_refused(self):
        restore=self.deployment.RUNS/RUN/'restore';restore.mkdir()
        with self.assertRaises(Exception):self.observe()
        restore.rmdir()
        path=self.deployment.RUNS/RUN/'install'/'after.bin'
        with path.open('r+b') as out:out.write(b'changed')
        with self.assertRaises(Exception):self.observe()
        self.assertFalse(self.calls())

    def test_host_source_and_measurement_source_drift(self):
        self.source_sha='0'*64
        with self.assertRaises(t.Refused):self.observe()
        source=self.d/'wrong.py';source.write_text('raise Exception("must not compile")')
        # Exercise actual loader; no original edits.
        self.patches[2].stop()
        with patch.object(t,'MEASURE',source),self.assertRaises(t.Refused):t.load_reviewed()
        self.patches[2].start()
        self.assertFalse(self.calls())

    def test_manifest_and_adb_drift(self):
        self.patches[2].stop()
        fake=self.d/'build';fake.mkdir()
        with patch.object(t,'BUILD',fake),self.assertRaises(Exception):t.load_reviewed()
        self.patches[2].start()
        fakeadb=self.d/'adb';fakeadb.write_bytes(b'not adb')
        with patch.object(t,'ADB',fakeadb),self.assertRaises(t.Refused):self.observe()
        self.assertFalse(self.calls())

    def test_no_shell_v2_no_shell(self):
        self.mode('no_v2')
        with self.assertRaises(t.Refused):self.observe()
        self.assertEqual(len(self.calls()),2)

    def test_completion_fsync_failure_terminal_unknown(self):
        original=t.durable
        def fail(log,value):
            original(log,value)
            if value['result']=='OBSERVED_MATCH':raise OSError('injected fsync failure')
        with patch.object(t,'durable',side_effect=fail),self.assertRaises(t.Refused):self.observe()
        self.assertEqual([r['result'] for r in self.events()],['UNKNOWN','OBSERVED_MATCH','UNKNOWN'])

    def test_initial_evidence_failure_no_commands(self):
        with patch.object(t,'durable',side_effect=OSError('fixture failure')),self.assertRaises(OSError):self.observe()
        self.assertFalse(self.calls())

    def direct(self,mode,seconds=.25):
        self.mode(mode)
        # Local owned fake child bypasses only the argv substitution, never invokes ADB.
        with patch.object(subprocess,'Popen',self.popen):
            child=t.PipeStream([sys.executable,'-B',str(ROOT/'tests/fake_shell.py'),str(self.config),'direct'],time.monotonic()+seconds)
        self.children.append(child.proc)
        return child

    def test_stalled_reply_deadline_and_child_cleanup(self):
        child=self.direct('stall');start=time.monotonic()
        try:
            with self.assertRaises(TimeoutError):self.measure.measure(child,.25)
        finally:child.dispose()
        self.assertLess(time.monotonic()-start,1.6)
        self.assertEqual((self.d/'request.bin').read_bytes(),self.measure.REQUEST)

    def test_fragment_deadline_not_reset(self):
        child=self.direct('slow');start=time.monotonic()
        try:
            with self.assertRaises(TimeoutError):self.measure.measure(child,.25)
        finally:child.dispose()
        self.assertLess(time.monotonic()-start,1.6)

    def test_send_backpressure_deadline_and_cleanup(self):
        child=self.direct('backpressure');start=time.monotonic()
        try:
            child.settimeout(.25)
            with self.assertRaises(TimeoutError):child.sendall(bytes(2_000_000))
        finally:child.dispose()
        self.assertLess(time.monotonic()-start,1.6)

    def test_success_reply_without_exit_is_unknown(self):
        child=self.direct('hang_exit')
        try:
            self.measure.measure(child,.25)
            with self.assertRaises(TimeoutError):child.finish()
        finally:child.dispose()

    def test_invalid_deadline_no_children(self):
        for seconds in (0,-1,601,float('nan'),float('inf')):
            with self.assertRaises(t.Refused):t.observe(self.binding,NONCE,expected_source_sha256=self.source_sha,seconds=seconds)
        self.assertFalse(self.calls())

    def test_send_boundary_source_drift_sends_no_request(self):
        original=t.verify_self
        count=0
        def guard(expected):
            nonlocal count
            count+=1
            if count==7:raise t.Refused('source drift at request boundary')
            original(expected)
        with patch.object(t,'verify_self',side_effect=guard),self.assertRaises(t.Refused):self.observe()
        self.assertFalse((self.d/'request.bin').exists())
        self.assertEqual(sum('shell' in a for a in self.calls()),1)

    def test_completion_conjunction_lost_nonzero_mismatch_or_truncation_unknown(self):
        result=self.observe();stdout=json.dumps(result).encode()
        self.assertEqual(t.accept_completion(self.binding,exit_status=0,stdout=stdout,
                         expected_source_sha256=self.source_sha),result)
        for status,out in ((None,stdout),(1,stdout),(0,b''),(0,b'{'),
                           (0,json.dumps(dict(result,wire_opcode=3)).encode())):
            with self.subTest(status=status),self.assertRaises(Exception):
                t.accept_completion(self.binding,exit_status=status,stdout=out,expected_source_sha256=self.source_sha)
        path=Path(result['terminal_evidence']);raw=path.read_bytes()
        for bad in (raw[:-1],raw+b'{"result":"UNKNOWN"}\n',raw+b'{'):
            path.write_bytes(bad)
            with self.assertRaises(Exception):
                t.accept_completion(self.binding,exit_status=0,stdout=stdout,expected_source_sha256=self.source_sha)
        path.write_bytes(raw)

    def test_shared_mutation_lock_blocks_before_commands(self):
        import fcntl
        with self.lock.open('r+') as stream:
            fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
            with self.assertRaises(BlockingIOError):self.observe()
        self.assertFalse(self.calls())

    def test_usb_change_at_send_boundary_zero_protocol_bytes(self):
        original=t.select_usb
        count=0
        def selected(raw,binding):
            nonlocal count
            count+=1
            if count==3:raw=raw.replace(b'transport_id:17',b'transport_id:18')
            return original(raw,binding)
        with patch.object(t,'select_usb',side_effect=selected),self.assertRaises(t.Refused):self.observe()
        self.assertFalse((self.d/'request.bin').exists())
        self.assertEqual(sum('shell' in a for a in self.calls()),1)

    def test_existing_server_lost_or_mismatched_stops_without_cli(self):
        with patch.object(t,'server_version',side_effect=t.Refused('wrong server')),self.assertRaises(t.Refused):
            self.observe()
        self.assertFalse(self.calls())

    def test_host_version_probe_socketpair_fragmentation_and_bad_versions(self):
        self.patches[4].stop()
        try:
            for reply in (b'OKAY00040029',b'OKAY00040028',b'FAIL0004nope',b'OKAY00040029X',b'OKAY'):
                host,peer=socket.socketpair();requests=[]
                def serve():
                    try:
                        data=b''
                        while len(data)<16:
                            data+=peer.recv(16-len(data))
                        requests.append(data)
                        for byte in reply:peer.sendall(bytes([byte]))
                    except BrokenPipeError:pass
                    finally:peer.close()
                worker=threading.Thread(target=serve);worker.start()
                with patch.object(socket,'create_connection',return_value=host) as connect:
                    if reply==b'OKAY00040029':t.server_version(time.monotonic()+1)
                    else:
                        with self.assertRaises(t.Refused):t.server_version(time.monotonic()+1)
                    connect.assert_called_once()
                    self.assertEqual(connect.call_args.args[0],('127.0.0.1',5037))
                worker.join(timeout=1);self.assertFalse(worker.is_alive())
                self.assertEqual(requests,[b'000chost:version'])
        finally:self.patches[4].start()

    def test_pipe_setup_failure_cleans_already_spawned_child(self):
        self.mode('backpressure')
        with patch.object(os,'set_blocking',side_effect=OSError('setup fixture failure')):
            with self.assertRaises(OSError):t.PipeStream([str(t.ADB),'direct'],time.monotonic()+1)
        self.assertEqual(len(self.children),1)
        self.assertIsNotNone(self.children[0].poll())

    def test_install_consumed_at_send_boundary_no_protocol_or_followup(self):
        original=self.deployment.check_install;count=0
        def check(*args,**kwargs):
            nonlocal count
            count+=1
            if count==7:(self.deployment.RUNS/RUN/'restore').mkdir()
            return original(*args,**kwargs)
        with patch.object(self.deployment,'check_install',side_effect=check),self.assertRaises(t.Refused):self.observe()
        self.assertFalse((self.d/'request.bin').exists())
        self.assertEqual(self.calls()[-1][-2:],['devices','-l'])

    def test_uncertainty_consumes_session_before_any_retry(self):
        self.unknown('remote_nonzero');count=len(self.calls())
        with self.assertRaises(FileExistsError):self.observe()
        self.assertEqual(len(self.calls()),count)

    def dispatch_expiry(self, *, after_wait=False, wall_only=False):
        real_wall,real_mono=time.time,time.monotonic
        offset=0.0;probes=0;sends=[];real_write=os.write;original_events=t.PipeStream._events
        self.binding=dataclasses.replace(self.binding,created_wall=real_wall()-179,created_monotonic=real_mono()-179)
        def probe(deadline):
            nonlocal probes,offset
            probes+=1
            if probes==6 and not after_wait:offset=1.5
        def events(child):
            nonlocal offset
            ready=original_events(child)
            if after_wait and child.before_write.__name__=='dispatch_fresh' and any(k.data=='stdin' for k,_ in ready):offset=1.5
            return ready
        def write(fd,data):
            if bytes(data)==self.measure.REQUEST:sends.append(bytes(data))
            return real_write(fd,data)
        with patch.object(time,'time',side_effect=lambda:real_wall()+offset),patch.object(time,'monotonic',side_effect=lambda:real_mono()+(0 if wall_only else offset)),patch.object(t,'server_version',side_effect=probe),patch.object(t.PipeStream,'_events',events),patch.object(os,'write',side_effect=write):
            with self.assertRaises(t.Refused):self.observe()
        self.assertFalse(sends)
        self.assertFalse((self.d/'request.bin').exists())
        self.assertEqual(self.events()[-1]['result'],'UNKNOWN')
        before=len(self.children)
        with self.assertRaises(FileExistsError):self.observe()
        self.assertEqual(len(self.children),before)

    def test_expired_during_final_server_probe_sends_zero_bytes(self):self.dispatch_expiry()
    def test_expired_during_writable_wait_sends_zero_bytes(self):self.dispatch_expiry(after_wait=True)
    def test_wall_expiry_after_final_guards_sends_zero_bytes(self):self.dispatch_expiry(wall_only=True)

    def test_write_boundary_callback_follows_writable_wait(self):
        child=self.direct('backpressure',1);seen=[];original_events=child._events
        def ready():
            value=original_events();seen.append('writable');return value
        def guard():
            self.assertEqual(seen,['writable']);seen.append('gate');raise t.Refused('write boundary fixture')
        child._events=ready;child.before_write=guard
        try:
            with self.assertRaises(t.Refused):child.sendall(self.measure.REQUEST)
        finally:child.dispose()
        self.assertEqual(seen,['writable','gate']);self.assertFalse((self.d/'request.bin').exists())

    def test_fresh_dispatch_may_complete_after_binding_age_limit(self):
        real_wall,real_mono=time.time,time.monotonic;real_write=os.write;offset=0.0;sends=[]
        self.binding=dataclasses.replace(self.binding,created_wall=real_wall()-179,created_monotonic=real_mono()-179)
        def write(fd,data):
            nonlocal offset
            if bytes(data)==self.measure.REQUEST:
                sends.append((time.time()-self.binding.created_wall,time.monotonic()-self.binding.created_monotonic));n=real_write(fd,data);offset=1.5;return n
            return real_write(fd,data)
        with patch.object(time,'time',side_effect=lambda:real_wall()+offset),patch.object(time,'monotonic',side_effect=lambda:real_mono()+offset),patch.object(os,'write',side_effect=write):
            result=self.observe()
            self.assertGreater(time.monotonic()-self.binding.created_monotonic,180)
            self.assertEqual(t.accept_completion(self.binding,exit_status=0,stdout=json.dumps(result).encode(),expected_source_sha256=self.source_sha),result)
        self.assertEqual(len(sends),1);self.assertTrue(all(0<=age<=180 for age in sends[0]))

    def test_readme_recipe_uses_real_loaded_source_attribute(self):
        import ast
        recipe=(ROOT/'README.md').read_text().split('```python\n')[1].split('```')[0]
        first=next(n for n in ast.parse(recipe).body if isinstance(n,ast.Assert))
        exec(compile(ast.Module(body=[first],type_ignores=[]),'<README assertion>','exec'),dict(transport=t,TRANSPORT_SHA=self.source_sha))

if __name__=='__main__':
    print('Preserved fixtures:',BASE,flush=True)
    result=unittest.main(verbosity=2,exit=False)
    print('Host parent peak RSS (platform units):',resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,flush=True)
    raise SystemExit(not result.result.wasSuccessful())
