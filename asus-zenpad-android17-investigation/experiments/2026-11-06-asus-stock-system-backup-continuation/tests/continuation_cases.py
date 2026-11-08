"""Additional offline fixtures, loaded by the audited test runner."""
import copy
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import unittest
from unittest.mock import patch

import policy as p
import stock_system_backup as c
import remote_worker as r
import continuation as cont
import health

# Set by the main test runner, avoiding a second module/test-runner import.
base = None


class PrefixTests(unittest.TestCase):
    def setUp(self):
        base.BackupTests.setUp(self)
    def tearDown(self):
        base.BackupTests.tearDown(self)
    def fixture(self):
        inputs = base.fixture_input(self.payload)
        r.dispatch(dict(operation='begin', run=base.RUN), io.BytesIO())
        return inputs
    def reuse(self, inputs):
        return r.dispatch(dict(operation='reuse', run=base.RUN, source_run=base.OLD,
                               chunks=inputs['chunks'], reviewed_input_sha256=p.sha(p.encoded(inputs))), io.BytesIO())

    def test_copy_reads_actual_prefix_and_preserves_old_inode_and_bytes(self):
        with base.small_geometry():
            inputs=self.fixture()
            old=self.remote/base.OLD/'chunk-0000.bin'
            before=r.identity(old.stat())
            result=self.reuse(inputs)
            new=self.remote/base.RUN/old.name
            self.assertEqual(old.read_bytes(),new.read_bytes())
            self.assertEqual(r.identity(old.stat()),before)
            self.assertNotEqual(old.stat().st_ino,new.stat().st_ino)
            self.assertEqual(old.stat().st_nlink,1)
            self.assertEqual(result['receipts'][0]['source']['sha256'],inputs['chunks'][0]['sha256_a'])

    def test_missing_corrupt_short_symlink_mode_owner_hardlink_prefix_fail_closed(self):
        for fault in ('missing','corrupt','short','symlink','mode','owner','hardlink'):
            folder=self.root/fault
            folder.mkdir(mode=0o700)
            with patch.object(r,'REMOTE_BASE',folder/'remote'),base.small_geometry():
                inputs=base.fixture_input(self.payload)
                r.dispatch(dict(operation='begin',run=base.RUN),io.BytesIO())
                old=r.REMOTE_BASE/base.OLD/'chunk-0000.bin'
                original=old.read_bytes()
                if fault == 'missing': old.unlink()
                if fault == 'corrupt': old.write_bytes(b'z'*1024)
                if fault == 'short': old.write_bytes(original[:-1])
                if fault == 'symlink':
                    old.unlink();old.symlink_to(folder/'missing')
                if fault == 'mode': old.chmod(0o644)
                if fault == 'hardlink': os.link(old,folder/'other-link')
                if fault == 'owner':
                    real_private=r.private
                    def reject(path, directory=False):
                        if Path(path) == old: raise p.Stop('wrong owner fixture')
                        return real_private(path,directory)
                    with patch.object(r,'private',side_effect=reject),self.assertRaises(p.Stop): self.reuse(inputs)
                else:
                    with self.assertRaises((p.Stop,FileNotFoundError)): self.reuse(inputs)
                self.assertFalse((r.REMOTE_BASE/base.RUN/'READY.json').exists())

    def test_prefix_replacement_during_copy_detected(self):
        with base.small_geometry():
            inputs=self.fixture()
            old=self.remote/base.OLD/'chunk-0000.bin'
            def replace(b):
                old.rename(old.with_suffix('.retained'))
                p.create_file(old,b)
            with self.assertRaises(p.Stop):
                r.read_actual(old,1024,inputs['chunks'][0]['sha256_a'],replace)
            self.assertTrue(old.with_suffix('.retained').exists())

    def test_reuse_collision_keeps_both_old_and_new(self):
        with base.small_geometry():
            inputs=self.fixture();self.reuse(inputs)
            old=(self.remote/base.OLD/'chunk-0000.bin').read_bytes()
            new=(self.remote/base.RUN/'chunk-0000.bin').read_bytes()
            with self.assertRaises(FileExistsError): self.reuse(inputs)
            self.assertEqual((self.remote/base.OLD/'chunk-0000.bin').read_bytes(),old)
            self.assertEqual((self.remote/base.RUN/'chunk-0000.bin').read_bytes(),new)

    def test_changed_reused_prefix_before_finalize_prevents_publication(self):
        owner=self
        class Changed(base.FilesystemRemote):
            def call(self,operation,**fields):
                if operation == 'finalize':
                    (owner.remote/base.RUN/'chunk-0000.bin').write_bytes(b'z'*1024)
                return super().call(operation,**fields)
        with base.small_geometry(),self.assertRaises(p.Stop):
            c.transfer(base.RUN,self.local,base.ByteDevice(self.payload),Changed(),self.journal,base.CODE_HASHES,base.fixture_input(self.payload))
        self.assertFalse((self.remote/base.RUN/'READY.json').exists())
        self.assertFalse((self.local/'COMPLETE.json').exists())
        self.assertEqual((self.remote/base.OLD/'chunk-0000.bin').read_bytes(),self.payload[:1024])

    def test_independent_verify_reads_every_chunk_and_entire_image(self):
        with base.small_geometry():
            result=c.transfer(base.RUN,self.local,base.ByteDevice(self.payload),base.FilesystemRemote(),self.journal,base.CODE_HASHES,base.fixture_input(self.payload))
            actual=r.read_actual
            with patch.object(r,'read_actual',wraps=actual) as reads:
                r.dispatch(dict(operation='verify',run=base.RUN,manifest_sha256=result['manifest_sha256']),io.BytesIO())
            self.assertEqual([Path(x.args[0]).name for x in reads.call_args_list],
                             ['chunk-0000.bin','chunk-0001.bin','chunk-0002.bin','chunk-0003.bin','system.img'])
            self.assertEqual(sum(x.args[1] for x in reads.call_args_list),len(self.payload)*2)

    def test_geometry_gap_overlap_missing_and_false_provenance_refused(self):
        with base.small_geometry():
            inputs=self.fixture()
            for edit in (lambda x:x[0].update(offset=1),lambda x:x[0].update(index=1),
                         lambda x:x.append(copy.deepcopy(x[0])),lambda x:x[0].update(bytes=1000),
                         lambda x:x[0]['source_capture'].update(transport=dict(kind='adb-tcp',endpoint='wrong',secure_adb='1')),
                         lambda x:x[0].update(sha256_b='0'*64),lambda x:x.clear()):
                rows=copy.deepcopy(inputs['chunks']);edit(rows)
                with self.assertRaises(p.Stop): p.validate_rows(rows)

    def test_unacknowledged_put_only_reusable_after_full_actual_verification(self):
        with base.small_geometry():
            inputs=self.fixture()
            # Treat existing source chunk as an upload whose acknowledgement was
            # lost. Same full verifier is used; no offset/resume/append exists.
            result=self.reuse(inputs)
            self.assertEqual(result['receipts'][0]['copied']['bytes'],1024)
        # Partial and hash-corrupt files are covered in the paired failure cases.


class CliTests(unittest.TestCase):
    def setUp(self): base.BackupTests.setUp(self)
    def tearDown(self): base.BackupTests.tearDown(self)

    def prepare_fixture(self):
        inputs=base.fixture_input(self.payload)
        for name in ('evidence','evidence/runs','evidence/inputs'):
            (self.local/name).mkdir(mode=0o700)
        digest=p.sha(p.encoded(inputs))
        p.create_file(self.local/'evidence/inputs'/(digest+'.json'),p.encoded(inputs))
        return inputs,digest

    def test_main_backup_and_separate_verify_execute_path_with_offline_transports(self):
        with base.small_geometry():
            inputs,digest=self.prepare_fixture()
            device=base.ByteDevice(self.payload)
            device.preflight=lambda:None
            remote=base.FilesystemRemote()
            args=['backup','--run-id',base.RUN,'--input-sha256',digest,'--execute',
                  '--reviewed-inputs','--stock-unchanged-since-capture','--exclusive-device-owner']
            with patch.object(c,'SPIKE',self.local),patch.object(c,'local_inputs',return_value=base.CODE_HASHES),                 patch.object(cont,'validate_input',return_value=inputs),patch.object(c,'Device',return_value=device) as new_device,                 patch.object(c,'Remote',return_value=remote),patch('sys.stdout',io.StringIO()):
                self.assertEqual(c.main(args),0)
                folder=self.local/'evidence/runs'/base.RUN
                self.assertTrue((folder/'COMPLETE.json').exists())
                manifest=p.sha((folder/'manifest.json').read_bytes())
                self.assertEqual(c.main(['verify','--run-id',base.RUN,'--manifest-sha256',manifest,
                                         '--execute','--exclusive-device-owner']),0)
                self.assertEqual(new_device.call_count,1)
                verification=list((self.local/'evidence/runs').glob(base.RUN+'-verify-*/VERIFIED.json'))
                self.assertEqual(len(verification),1)
                with self.assertRaises(p.Stop):
                    c.main(['verify','--run-id',base.RUN,'--manifest-sha256','0'*64,
                            '--execute','--exclusive-device-owner'])
            self.assertEqual(remote.calls[-1],'verify')

    def test_full_geometry_metadata_fits_bounded_ssh_argv_and_decodes_locally(self):
        import shlex
        remote=c.Remote(base.RUN,None)
        rows=[]
        for i,o,n in p.chunk_layout():
            digest=p.sha(str(i).encode())
            rows.append(dict(index=i,offset=o,bytes=n,sha256_a=digest,sha256_b=digest,remote_sha256=digest,
                             source_capture=dict(run=base.RUN,transport=p.TRANSPORT,source_code_sha256=c.local_inputs(),
                                                 helper_sha256=c.HELPER_HASH,root_binary_sha256=c.ROOT_BINARY_HASH,
                                                 receipt_sha256=p.sha(('receipt'+str(i)).encode()))))
        q=dict(operation='assemble',run=base.RUN,chunks=rows)
        packed=c.pack_request(q)
        command=shlex.join(['python3','-c',remote.code,packed])
        self.assertLess(len(command.encode()),65536)
        script=c.REQUEST_BOOTSTRAP+'print(sys.argv[1])'
        result=subprocess.run([sys.executable,'-c',script,packed],text=True,capture_output=True,check=True)
        self.assertEqual(json.loads(result.stdout),q)
        bomb=c.base64.b64encode(c.zlib.compress(b'x'*(1024*1024+1))).decode()
        result=subprocess.run([sys.executable,'-c',script,bomb],text=True,capture_output=True)
        self.assertNotEqual(result.returncode,0)
        base.OBSERVATIONS.append(dict(case='maximal_full_geometry_metadata_transport',chunks=112,
                                      compact_json_bytes=len(json.dumps(q,separators=(',',':')).encode()),
                                      ssh_command_bytes=len(command.encode()),limit_bytes=65536))

    def test_every_parent_gate_required_before_transport(self):
        with base.small_geometry():
            inputs,digest=self.prepare_fixture()
            full=['backup','--run-id',base.RUN,'--input-sha256',digest,'--execute',
                  '--reviewed-inputs','--stock-unchanged-since-capture','--exclusive-device-owner']
            for remove in ('--reviewed-inputs','--stock-unchanged-since-capture','--exclusive-device-owner','--input-sha256'):
                args=list(full);args.remove(remove)
                if remove=='--input-sha256':args.remove(digest)
                with patch.object(c,'SPIKE',self.local),patch.object(c,'local_inputs',return_value=base.CODE_HASHES),                     patch.object(cont,'validate_input',return_value=inputs),patch.object(cont,'prepare',return_value=inputs),                     patch.object(c,'Remote',side_effect=AssertionError('transport before review')),self.assertRaises(p.Stop):
                    c.main(args)


class EvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.events=cont.load_events(cont.source_directory(cont.LEGACY_RUN))
        cls.bundle=cont.prepare()

    def test_actual_original_prefix_has_77_pinned_double_captures(self):
        self.assertEqual(len(self.bundle['chunks']),77)
        self.assertEqual(sum(x['bytes'] for x in self.bundle['chunks']),77*32*1024*1024)
        self.assertEqual(self.bundle['chunks'][-1]['index'],76)
        self.assertEqual(self.bundle['source_code_sha256'],cont.LEGACY_CODE)
        self.assertGreater(len(self.bundle['journal_sha256']),8500)
        self.assertEqual(cont.validate_input(self.bundle,p.sha(p.encoded(self.bundle))),self.bundle)

    def test_false_journal_identity_geometry_comparison_upload_or_guard_refused(self):
        kinds={}
        for i,x in enumerate(self.events): kinds.setdefault(x['event']['kind'],i)
        edits=[(0,lambda e:e['target'].update(serial='wrong')),
               (0,lambda e:e['source_code_sha256'].update(**{'policy.py':'0'*64})),
               (kinds['two_source_reads_verified'],lambda e:e.update(sha256='0'*64)),
               (kinds['source_read_staged'],lambda e:e.update(offset=1)),
               (kinds['binary_received'],lambda e:e.update(bytes=1)),
               (kinds['chunk_verified'],lambda e:e.update(sha256_b='0'*64))]
        put=next(i for i,x in enumerate(self.events) if x['event']['kind']=='remote_dispatch' and x['event']['request']['operation']=='put')
        edits += [(put+1,lambda e:e.update(status=255)),(put+1,lambda e:e.update(stdout='{}'))]
        stage_dispatch=next(i for i,x in enumerate(self.events) if x['event']['kind']=='dispatch' and 'dd if=' in (x['event'].get('script') or ''))
        edits += [(stage_dispatch,lambda e:e.update(script=e['script'].replace('count=32','count=31'))),
                  (stage_dispatch+1,lambda e:e.update(stdout='lost nonce'))]
        for index,edit in edits:
            events=list(self.events)
            changed=copy.deepcopy(events[index]);edit(changed['event']);events[index]=changed
            with self.subTest(index=index),patch.object(cont,'load_events',return_value=events),self.assertRaises((p.Stop,KeyError)):
                cont.prepare()

    def test_pinned_input_rejects_false_rows_even_if_hash_recomputed(self):
        bad=copy.deepcopy(self.bundle)
        bad['chunks'][0]['sha256_a']='0'*64
        with self.assertRaises(p.Stop): cont.validate_input(bad,p.sha(p.encoded(bad)))
        with self.assertRaises(p.Stop): cont.validate_input(self.bundle,'0'*64)

    def test_missing_or_nonsequential_journal_fails(self):
        import tempfile
        with tempfile.TemporaryDirectory(dir=base.SPIKE/'tests') as d:
            folder=Path(d)
            p.create_file(folder/'00002-plan.json',p.encoded(dict(kind='plan')))
            with self.assertRaises(p.Stop):cont.load_events(folder)

    def test_cyclic_lineage_refused(self):
        with self.assertRaises(p.Stop):cont.prepare(cont.LEGACY_RUN,lineage=(cont.LEGACY_RUN,))

    def test_legacy_uncertain_export_cannot_be_promoted(self):
        with self.assertRaises(p.Stop):cont.prepare(include_uncertain=True)


class FutureContinuationTests(unittest.TestCase):
    def setUp(self):
        base.BackupTests.setUp(self)
        self.codes = patch.object(c, 'local_inputs', return_value=c.local_inputs())
        self.codes.start()
        # Seed prefix is a tiny synthetic already-reviewed capture, not a copy
        # of the 2.4 GiB real legacy prefix. Its recursive validator is isolated.
        self.prior = patch.object(cont, 'validate_input', side_effect=lambda bundle, expected, lineage=(): bundle)
        self.prior.start()
    def tearDown(self):
        self.prior.stop()
        self.codes.stop()
        base.BackupTests.tearDown(self)

    def run_failed_capture(self, fault):
        inputs=base.fixture_input(self.payload)
        code=c.local_inputs()
        p.create_file(self.local/'input.json',p.encoded(inputs))
        self.journal.event('plan',run=base.RUN,mode='EXECUTE',action='backup',target=p.TARGET,transport=p.TRANSPORT,
                           no_raw_block_writes=True,source_code_sha256=code,helper_sha256=c.HELPER_HASH,
                           root_binary_sha256=c.ROOT_BINARY_HASH,reviewed_input_sha256=p.sha(p.encoded(inputs)))
        journal=self.journal
        payload=self.payload
        class ReceiptDevice(base.ByteDevice):
            def stage(self,label,offset,length):
                super().stage(label,offset,length)
                d=c.Device(base.RUN,journal)
                def root(body):
                    token='f'*32
                    journal.event('dispatch',argv=[sys.executable,str(c.HELPER)],script=c.root_envelope(body,token))
                    out='ASUS_STAGE_INODE=123\nASUS_SYSTEM_RC_'+token+'=0\n'
                    journal.event('returned',status=0,stdout=out,stderr='')
                    return out
                d.root=root
                d.stage(label,offset,length)
            def binary(self,label,length,consume):
                journal.event('binary_dispatch',label=label,bytes=length)
                super().binary(label,length,consume)
                journal.event('binary_received',label=label,bytes=length)
        class ReceiptRemote(base.FilesystemRemote):
            def call(self,operation,**fields):
                q=dict(operation=operation,run=base.RUN,**fields)
                journal.event('remote_dispatch',request=q)
                result=r.dispatch(q,io.BytesIO())
                journal.event('remote_returned',status=0,stdout=json.dumps(result),stderr='')
                return result
            def put(self,index,path,length,digest):
                q=dict(operation='put',run=base.RUN,index=index,bytes=length,sha256=digest)
                journal.event('remote_dispatch',request=q)
                if fault == 'partial':
                    with self_error(p.Stop):r.dispatch(q,io.BytesIO(path.read_bytes()[:-1]))
                else:
                    with path.open('rb') as stream:result=r.dispatch(q,stream)
                if fault in ('lost','partial'):raise p.Stop('lost put response')
                journal.event('remote_returned',status=0,stdout=json.dumps(result),stderr='')
                return result['sha256']
        device=ReceiptDevice(payload)
        if fault == 'cleanup':
            device.clean_chunk=lambda: (_ for _ in ()).throw(p.Stop('cleanup completion uncertain'))
        with self.assertRaises(p.Stop):c.transfer(base.RUN,self.local,device,ReceiptRemote(),journal,code,inputs)
        return inputs

    def test_future_verified_prefix_includes_original_provenance_and_new_capture(self):
        with base.small_geometry(),patch.object(c,'BUFFER',256),patch.object(cont,'BUFFER',256):
            self.run_failed_capture('cleanup')
            with patch.object(cont,'source_directory',return_value=self.local):bundle=cont.prepare(base.RUN)
            self.assertEqual(len(bundle['chunks']),2)
            self.assertEqual(bundle['chunks'][0]['source_capture']['run'],base.OLD)
            self.assertEqual(bundle['chunks'][1]['source_capture']['run'],base.RUN)
            self.assertFalse(bundle['uncertain_last_put'])

    def test_future_prefix_requires_revalidation_of_prior_reviewed_inputs(self):
        with base.small_geometry(),patch.object(c,'BUFFER',256),patch.object(cont,'BUFFER',256):
            self.run_failed_capture('cleanup')
            with patch.object(cont,'source_directory',return_value=self.local),patch.object(cont,'validate_input',side_effect=p.Stop('prior source changed')) as prior,self.assertRaises(p.Stop):
                cont.prepare(base.RUN)
            self.assertEqual(prior.call_count,1)

    def test_lost_put_explicitly_inspected_and_partial_refused(self):
        for fault in ('lost','partial'):
            folder=self.root/fault;folder.mkdir(mode=0o700)
            self.local=folder/'local';self.local.mkdir(mode=0o700);self.journal=c.Journal(self.local)
            with patch.object(r,'REMOTE_BASE',folder/'remote'),base.small_geometry(),patch.object(c,'BUFFER',256),patch.object(cont,'BUFFER',256):
                self.run_failed_capture(fault)
                with patch.object(cont,'source_directory',return_value=self.local):
                    normal=cont.prepare(base.RUN)
                    inspected=cont.prepare(base.RUN,True)
                self.assertEqual(len(normal['chunks']),1)
                self.assertEqual(len(inspected['chunks']),2)
                self.assertTrue(inspected['uncertain_last_put'])
                new='20261106T200000Z-0123456789abcdef'
                r.dispatch(dict(operation='begin',run=new),io.BytesIO())
                q=dict(operation='reuse',run=new,source_run=base.RUN,chunks=inspected['chunks'],reviewed_input_sha256=p.sha(p.encoded(inspected)))
                if fault == 'lost':
                    result=r.dispatch(q,io.BytesIO())
                    self.assertEqual(len(result['receipts']),2)
                else:
                    with self.assertRaises(p.Stop):r.dispatch(q,io.BytesIO())
                self.assertTrue((r.REMOTE_BASE/base.RUN/'chunk-0001.bin').exists())


# A local assertion context used inside the mock, never a transport call.
class self_error:
    def __init__(self,expected):self.expected=expected
    def __enter__(self):return self
    def __exit__(self,kind,value,tb):
        if kind is None:raise AssertionError('Expected partial upload failure')
        return issubclass(kind,self.expected)


class HelperTests(unittest.TestCase):
    def setUp(self):
        spec=importlib.util.spec_from_file_location('offline_helper',c.HELPER)
        self.helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.helper)

    def test_fixed_helper_request_templates_and_arbitrary_input_refusal(self):
        bodies=[]
        d=c.Device(base.RUN,type('J',(),{'event':lambda *a,**k:None})())
        def root(body):
            bodies.append(body)
            return 'ASUS_STAGE_INODE=123\n'
        d.root=root
        d.preflight();d.setup();d.stage('a',0,c.CHUNK);d.stage('b',0,c.CHUNK);d.clean_chunk();d.finish()
        for body in bodies:
            request=c.root_envelope(body,'e'*32)
            c.validate_root_request(request)
            with self.assertRaises(p.Stop):c.validate_root_request(request+'echo unexpected\n')
        for request in ('dd if=/dev/zero of=/dev/block/mmcblk0p25', 'mount -o remount,rw /system', 'id'):
            with self.assertRaises(p.Stop):c.validate_root_request(request)

    def test_clone_preserves_inner_status_and_selinux_restore(self):
        for rc in (0,17):
            calls=[]
            def fake(argv,**kwargs):
                calls.append((argv,kwargs))
                if 'input' in kwargs:
                    script=kwargs['input']
                    self.assertIn("trap 'setenforce 1' EXIT",script)
                    token=re.search(r'ASUS_WIFI_ROOT_([0-9a-f]{32})=',script).group(1)
                    return subprocess.CompletedProcess(argv,rc,'ASUS_WIFI_ROOT_'+token+'='+str(rc)+'\n','')
                return subprocess.CompletedProcess(argv,0,'','')
            with patch.object(self.helper,'validate_root_request'),patch.object(self.helper,'healthy') as healthy,patch.object(self.helper.subprocess,'run',side_effect=fake),patch('sys.stdin',io.StringIO('echo fixture')),patch('sys.stdout',io.StringIO()),patch('sys.stderr',io.StringIO()):
                if rc:
                    with self.assertRaises(SystemExit) as exit:self.helper.main()
                    self.assertEqual(exit.exception.code,rc)
                else:self.assertEqual(self.helper.main(),0)
            self.assertEqual(healthy.call_count,2)
            self.assertEqual(sum('input' in kw for _,kw in calls),1)
            self.assertEqual(sum('push' in argv for argv,_ in calls),1)

    def test_clone_missing_nonce_timeout_or_push_failure_no_retry(self):
        for fault in ('nonce','timeout','push'):
            calls=[]
            def fake(argv,**kwargs):
                calls.append(argv)
                if 'push' in argv and fault=='push':raise subprocess.CalledProcessError(255,argv)
                if 'input' in kwargs and fault=='timeout':raise subprocess.TimeoutExpired(argv,75)
                return subprocess.CompletedProcess(argv,0,'','')
            with patch.object(self.helper,'validate_root_request'),patch.object(self.helper,'healthy'),patch.object(self.helper.subprocess,'run',side_effect=fake),patch('sys.stdin',io.StringIO('echo fixture')),patch('sys.stdout',io.StringIO()),patch('sys.stderr',io.StringIO()):
                with self.assertRaises((SystemExit,subprocess.SubprocessError)):self.helper.main()
            self.assertEqual(sum('push' in argv for argv in calls),1)
            self.assertLessEqual(sum(any('timeout 60' in a for a in argv) for argv in calls),1)
