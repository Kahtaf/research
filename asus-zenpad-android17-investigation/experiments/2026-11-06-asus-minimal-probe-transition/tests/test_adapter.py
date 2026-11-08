import contextlib
import copy
import io
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
import adapter as a
import engine_fake as f
b = a.b
f.c = b
RUN = '9b95c5c6-cae1-44c9-bf02-1f6159a3dce7'
BOOT = '06f0f8d8-1729-48a9-b141-2728e5ae8f81'
SCENARIOS = []
ROW = dict(serial=b.SERIAL, state='device', usb='1-3.2', product='WW_P00A', model='P00A', device='P00A_2', transport_id='12')


def contract(phase):
    c = a.contract_template(RUN, phase)
    c.update(parent_technical_review=True, reviewer='OFFLINE FIXTURE', reference='not a physical approval',
             supervised_manual_entry_return_plan=True, issued_at=time.time()-1, valid_until=time.time()+120)
    return c


def pin():
    return dict(schema=2, profile=a.PROFILE, run_id=RUN, code_sha256=a.code_receipt()['sha256'],
                candidate_sha256=a.IMAGE_SHA, full_p10_sha256=a.FULL_SHA, created_at=time.time(),
                created_monotonic=time.monotonic(), host_clock_epoch=a.host_clock_epoch(),
                stock=ROW.copy(), properties=a.PROPS.copy(), enforcing=True, boot_id=BOOT)


class Fake:
    """Actual pinned helper runs; model only the individual subprocess boundary."""
    def __init__(self, stock, fault=None):
        self.inner = f.FakeAdbRoot(stock, fault=fault)
        self.inner.props.update(a.PROPS)
        self.row = ROW.copy()
        self.calls = []
        self.before = None
        self.stderr = ''
        self.root_exception = None
        self.missing_wifi = False

    def __call__(self, argv, *, input=None, **kwargs):
        if self.before:
            self.before(argv, input)
        self.calls.append((list(argv), input))
        def result(out='', err=''):
            return subprocess.CompletedProcess(argv, 0, out, err)
        if argv == ['adb','devices','-l']:
            row = self.row
            fields = ' '.join(k+':'+v for k,v in row.items() if k not in ('serial','state'))
            return result('List of devices attached\n'+row['serial']+' '+row['state']+' '+fields+'\n'+
                          b.ENDPOINT+' device product:WW_P00A model:P00A device:P00A_2 transport_id:50\n')
        if argv[:2] == ['adb','-t']:
            args = argv[3:]
            if args[:2] == ['shell','getprop']:
                return result(self.inner.props[args[2]]+'\n')
            if args == ['shell','getenforce']:
                return result(self.inner.selinux+'\n')
            if args == ['shell','cat','/proc/sys/kernel/random/boot_id']:
                return result(BOOT+'\n')
            raise AssertionError(argv)
        assert argv[:3] == ['adb','-s',b.ENDPOINT], argv
        args = argv[3:]
        if args == ['shell','cat','/proc/sys/kernel/random/boot_id']:
            return result(BOOT+'\n')
        if args[:1] == ['shell'] and len(args) == 2 and args[1].startswith('set -eu'):
            return result('', self.stderr)
        if args[:1] == ['push'] and args[1] == str(b.ROOT_BINARY):
            return result('root binary staged\n', self.stderr)
        if args == ['shell','chmod','700','/data/local/tmp/asus-mtk-su64']:
            return result('', self.stderr)
        if args[:1] == ['shell'] and len(args) == 2 and args[1].startswith('timeout 60 '):
            if self.root_exception:
                raise self.root_exception
            session = re.search(re.escape(b.BASE)+r'/exact-ramusb-[0-9a-f-]+-(?:install|restore)',input)
            assert session, input
            self.inner.session = session.group(0)
            p = self.inner([sys.executable,str(b.HELPER)], input=input)
            token = re.search(r'ASUS_WIFI_ROOT_([0-9a-f]{32})=',input).group(1)
            out = p.stdout if self.missing_wifi else p.stdout+f'\nASUS_WIFI_ROOT_{token}=0\n'
            return subprocess.CompletedProcess(argv,p.returncode,out,p.stderr+self.stderr)
        return self.inner(argv,input=input,**kwargs)


class Cases(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stock, cls.full, cls.local = a.verify_local()
        cls.image = a.read(a.IMAGE)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=a.ROOT/'evidence', prefix='test-')
        self.addCleanup(self.tmp.cleanup)
        self.directory = Path(self.tmp.name)
        self.patch_runs = patch.object(a,'RUNS',self.directory/'runs')
        self.patch_runs.start()
        self.addCleanup(self.patch_runs.stop)
        self.fake = Fake(self.stock)

    def cli(self, args):
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = a.main(args)
        return code,stdout.getvalue(),stderr.getvalue()

    def invoke(self, phase):
        path = self.directory/(phase+'-contract.json')
        c=contract(phase)
        if phase in ('pin-restore','restore'):c['install_completion_token']=self.install_token
        a.durable(path,c)
        with patch.object(subprocess,'run',side_effect=self.fake), patch.object(b,'EXECUTE_LOCK',self.directory/'lock'):
            (self.directory/'lock').touch(exist_ok=True)
            code,out,err = self.cli([phase,'--execute','--run-id',RUN,'--contract',str(path),
                                     '--supervised','--physical-fallback-present'])
        self.assertEqual(code,0,(phase,out,err))
        if phase=='install':self.install_token=json.loads(out)['install_completion_token']
        return a.json_file(a.RUNS/RUN/phase/'state.json')

    def run_engine(self, fault=None, action='install', initial=None):
        directory=self.directory/'phase'; directory.mkdir()
        p=pin(); g=a.Guard(contract(action),RUN,action,a.code_receipt()['sha256'],p)
        j=a.Journal(directory,action,RUN,g.code); j.state['pin']=p; j.save()
        t=a.Transport(directory,j,action,g)
        self.fake=Fake(self.stock if initial is None else initial,fault)
        with patch.object(subprocess,'run',side_effect=self.fake):
            state=a.execute(action,self.stock,self.full,t,j)
        SCENARIOS.append(dict(fault=fault, action=action, state=copy.deepcopy(state),
                              modeled_writes=copy.deepcopy(self.fake.inner.writes), commands=len(self.fake.calls),
                              evidence_kind='subprocess-blocked fixture only; not physical capture'))
        return state,t

    def test_exact_new_image_and_zero_padding(self):
        self.assertEqual(a.sha(a.admit(self.image,self.stock)),a.FULL_SHA)
        self.assertFalse(self.local['target_is_zero_record'])
        self.assertFalse(self.local['bounded_automatic_return_claim'])

    def test_old_candidate_refused(self):
        old=a.WORKSPACE/'2026-11-06-asus-linux49-probe-initrd-fix/artifacts/probe-r3/UNTESTED-combined-linux49-ram-probe-r3.img'
        with self.assertRaises(b.Refused): a.admit(a.read(old),self.stock)

    def test_header_kernel_geometry_and_padding_mutations(self):
        for offset in (0,8,20,36,64,2048,2052,2600,len(self.image)-1):
            data=bytearray(self.image);data[offset]^=1
            with self.subTest(offset=offset),self.assertRaises(b.Refused):a.admit(bytes(data),self.stock)
        for data in (self.full[:-1],self.full+b'\0',self.full[:-1]+b'\1'):
            with self.assertRaises(b.Refused):a.admit(self.image,self.stock,data)

    def test_default_plan_and_execute_refusal_no_commands(self):
        with patch.object(subprocess,'run',side_effect=AssertionError('no actual subprocess')):
            self.assertEqual(self.cli(['install'])[0],0)
            self.assertEqual(self.cli(['verify-local'])[0],0)
            self.assertEqual(self.cli(['install','--execute'])[0],2)
            self.assertEqual(self.cli(['plan','--execute'])[0],2)

    def test_template_no_approval_or_physical_flags(self):
        c=a.contract_template(RUN,'install')
        self.assertFalse(c['parent_technical_review']);self.assertIsNone(c['valid_until'])
        self.assertFalse(c['supervised_manual_entry_return_plan'])

    def test_missing_review_supervision_and_bounded_contract(self):
        for change in ({'parent_technical_review':False},{'supervised_manual_entry_return_plan':False},
                       {'reviewer':''},{'reference':''},{'issued_at':None},{'valid_until':time.time()-1},
                       {'valid_until':time.time()+1000},{'code_sha256':'wrong'},{'profile_sha256':'wrong'}):
            c=contract('install');c.update(change)
            with self.subTest(change=change),self.assertRaises(b.Refused):a.Guard(c,RUN,'install',a.code_receipt()['sha256'],pin())

    def test_fresh_pin_identity_and_topology(self):
        for change in ({'created_at':time.time()-181},{'created_at':time.time()+10},{'enforcing':False},
                       {'candidate_sha256':'45551fec'},{'properties':{}},{'stock':{**ROW,'serial':'other'}}):
            p=pin();p.update(change)
            with self.subTest(change=change),self.assertRaises(b.Refused):a.validate_pin(p,RUN,a.code_receipt()['sha256'])

    def test_full_install_and_linked_capture(self):
        state,t=self.run_engine()
        self.assertEqual(state['outcome'],'installed_full_hash_verified')
        self.assertTrue(state['partition_may_be_modified'])
        self.assertFalse(state['restore_verified'])
        self.assertEqual([w['source'] for w in self.fake.inner.writes],['candidate'])
        a.verify_capture(t.directory,state,a.FULL_SHA)
        self.assertFalse(state['manual_entered']);self.assertFalse(state['probe_report_observed'])

    def test_known_completed_partial_one_inverse(self):
        state,t=self.run_engine('partial')
        self.assertEqual(state['outcome'],'install_failed_fixed_inverse_verified')
        self.assertEqual([w['source'] for w in self.fake.inner.writes],['candidate','stock'])
        self.assertFalse(state['partition_may_be_modified']);self.assertTrue(state['restore_verified'])

    def test_candidate_full_readback_mismatch_one_inverse(self):
        state,t=self.run_engine('mismatch')
        self.assertEqual(state['outcome'],'install_failed_fixed_inverse_verified')
        self.assertEqual([w['source'] for w in self.fake.inner.writes],['candidate','stock'])

    def test_staging_full_mismatch_prevents_write(self):
        state,t=self.run_engine('staging_corruption')
        self.assertEqual(state['outcome'],'refused_or_failed_stop');self.assertFalse(self.fake.inner.writes)

    def test_install_stock_prerequisite(self):
        state,t=self.run_engine(initial=self.full)
        self.assertEqual(state['outcome'],'refused_or_failed_stop');self.assertFalse(self.fake.inner.writes)
        self.assertTrue(state['partition_may_be_modified'])

    def test_restore_only_exact_candidate_or_original(self):
        state,t=self.run_engine(action='restore',initial=bytes(b.SIZE))
        self.assertEqual(state['outcome'],'refused_or_failed_stop');self.assertFalse(self.fake.inner.writes)
        self.assertTrue(state['partition_may_be_modified'])

    def test_restore_candidate(self):
        state,t=self.run_engine(action='restore',initial=self.full)
        self.assertEqual(state['outcome'],'restored_full_hash_verified')
        self.assertEqual([w['source'] for w in self.fake.inner.writes],['stock'])
        self.assertFalse(state['partition_may_be_modified'])

    def test_restore_already_original(self):
        state,t=self.run_engine(action='restore')
        self.assertEqual(state['outcome'],'verified_already_original');self.assertFalse(self.fake.inner.writes)
        self.assertTrue(state['restore_verified']);self.assertFalse(state['partition_may_be_modified'])

    def test_uncertain_after_candidate_no_later_commands(self):
        for fault in ('lost_write','lost_readback','missing_status','helper_failed'):
            with self.subTest(fault=fault):
                # use a fresh local phase per scenario
                phase=self.directory/'phase'
                if phase.exists():
                    import shutil;shutil.rmtree(phase)
                state,t=self.run_engine(fault)
                self.assertEqual(state['outcome'],'terminal_uncertainty_no_commands')
                self.assertEqual([w['source'] for w in self.fake.inner.writes],['candidate'])
                count=len(self.fake.calls)
                with self.assertRaises(b.UncertainTransport):t.cleanup()
                self.assertEqual(len(self.fake.calls),count)
                self.assertTrue(state['partition_may_be_modified'])

    def test_inverse_failure_retains_modified_status(self):
        state,t=self.run_engine('inverse_failure')
        self.assertEqual(state['outcome'],'inverse_unverified_stop')
        self.assertEqual([w['source'] for w in self.fake.inner.writes],['candidate','stock'])
        self.assertTrue(state['partition_may_be_modified'])

    def test_restore_failure_retains_existing_modified_status(self):
        state,t=self.run_engine('restore_failure',action='restore',initial=self.full)
        self.assertEqual(state['outcome'],'refused_or_failed_stop')
        self.assertTrue(state['partition_may_be_modified'])

    def make_transport(self):
        directory=self.directory/'boundary';directory.mkdir()
        g=a.Guard(contract('install'),RUN,'install',a.code_receipt()['sha256'],pin())
        j=a.Journal(directory,'install',RUN,g.code);j.state['pin']=g.pin;j.save()
        return a.Transport(directory,j,'install',g)

    def test_nested_helper_unicode_closed_and_timeout_terminal(self):
        for exc in (UnicodeError('decode'),OSError('closed transport'),ValueError('I/O operation on closed file'),
                    subprocess.TimeoutExpired(['fixture'],75)):
            with self.subTest(exc=exc):
                directory=self.directory/'boundary'
                if directory.exists():
                    import shutil;shutil.rmtree(directory)
                t=self.make_transport();self.fake=Fake(self.stock);self.fake.root_exception=exc
                with patch.object(subprocess,'run',side_effect=self.fake),self.assertRaises(b.UncertainTransport):t.setup()
                count=len(self.fake.calls)
                with self.assertRaises(b.UncertainTransport):t.cleanup()
                self.assertEqual(len(self.fake.calls),count);self.assertTrue(t.guard.stopped)

    def test_helper_missing_completion_stops_no_cleanup(self):
        t=self.make_transport();self.fake.missing_wifi=True
        with patch.object(subprocess,'run',side_effect=self.fake),self.assertRaises(b.UncertainTransport):t.setup()
        self.assertTrue(t.guard.stopped)

    def test_nested_staging_expiry_checked_after_evidence_before_dispatch(self):
        t=self.make_transport();original=a.durable
        def durable(path,value):
            original(path,value)
            if value.get('argv') == ['adb','-s',b.ENDPOINT,'push',str(b.ROOT_BINARY),'/data/local/tmp/asus-mtk-su64']:
                t.guard.contract['valid_until']=time.time()-1
        with patch.object(a,'durable',side_effect=durable),patch.object(subprocess,'run',side_effect=self.fake),self.assertRaises(b.UncertainTransport):t.setup()
        self.assertFalse(any(x[0][3:4]==['push'] for x in self.fake.calls))
        count=len(self.fake.calls)
        with self.assertRaises(b.UncertainTransport):t.cleanup()
        self.assertEqual(len(self.fake.calls),count)

    def test_pin_expiry_inside_helper_before_candidate_dispatch(self):
        t=self.make_transport()
        def before(argv,script):
            if argv[3:5]==['shell','chmod']:
                t.guard.pin['created_at']=time.time()-181
        self.fake.before=before
        with patch.object(subprocess,'run',side_effect=self.fake),self.assertRaises(b.UncertainTransport):t.write('candidate')
        self.assertFalse(self.fake.inner.writes)
        self.assertFalse(t.journal.state['write_dispatches'])

    def test_expired_known_candidate_completion_forbids_inverse(self):
        t=self.make_transport()
        self.fake.inner.fault='partial'
        # Model an already-staged candidate; only the candidate write is requested.
        self.fake.inner.files[t.vault+'/candidate.bin']=self.full
        def before(argv,script):
            if script and 'dd if='+t.vault+'/candidate.bin of='+b.BLOCK in script:
                t.guard.contract['valid_until']=time.time()-1
        self.fake.before=before
        with patch.object(subprocess,'run',side_effect=self.fake),self.assertRaises(b.UncertainTransport):t.write('candidate')
        self.assertEqual([w['source'] for w in self.fake.inner.writes],['candidate'])
        count=len(self.fake.calls)
        with self.assertRaises(b.UncertainTransport):t.write('stock')
        self.assertEqual(count,len(self.fake.calls))

    def test_source_drift_stops_boundary(self):
        t=self.make_transport()
        with (patch.object(a,'check_sources',side_effect=b.Refused('source drift')),
              patch.object(subprocess,'run',side_effect=self.fake)):
            with self.assertRaises(b.UncertainTransport):t.usb_enumeration()
        self.assertFalse(self.fake.calls)

    def test_usb_topology_or_identity_change_stops_all(self):
        for change in ({'usb':'2-1'},{'serial':'other'},{'model':'other'},{'transport_id':'20'}):
            directory=self.directory/'boundary'
            if directory.exists():
                import shutil;shutil.rmtree(directory)
            t=self.make_transport();self.fake=Fake(self.stock);self.fake.row.update(change)
            with patch.object(subprocess,'run',side_effect=self.fake),self.assertRaises(b.UncertainTransport):t.setup()
            self.assertFalse(self.fake.inner.root_scripts)
            count=len(self.fake.calls)
            with self.assertRaises(b.UncertainTransport):t.cleanup()
            self.assertEqual(count,len(self.fake.calls))

    def test_aggregate_stderr_preserved(self):
        t=self.make_transport();self.fake.stderr='fixture stderr\n'
        import root_dispatch
        script=b.root_envelope('true', 'a'*32)
        # setup body is understood by storage fake
        with patch.object(subprocess,'run',side_effect=self.fake):
            t.setup()
        results=[a.json_file(p) for p in t.directory.glob('*-result.json')]
        self.assertTrue(any(r.get('stderr')=='fixture stderr\n' for r in results))
        completions=[e for e in t.journal.state['events'] if e['kind']=='pinned_helper_completion']
        self.assertEqual(completions[-1]['stderr'].count('fixture stderr\n'),4)
        self.assertIn('root binary staged',completions[-1]['stderr'])

    def test_cli_lifecycle_fresh_pin_changed_transport_and_consumed_restore(self):
        self.invoke('pin-install');installed=self.invoke('install')
        self.fake.row['transport_id']='23'
        self.invoke('pin-restore');restored=self.invoke('restore')
        self.assertEqual(restored['outcome'],'restored_full_hash_verified')
        self.assertFalse(restored['hardware_ready']);self.assertFalse(restored['stock_returned'])
        count=len(self.fake.calls)
        with self.assertRaises(b.Refused):a.check_install(RUN,a.code_receipt()['sha256'],getattr(self,'install_token',None))
        self.assertEqual(len(self.fake.calls),count)
        with self.assertRaises(FileExistsError):a.reserve(RUN,'install')

    def test_clean_install_linkage_required_and_capture_tamper_refused(self):
        self.invoke('pin-install');state=self.invoke('install')
        path=a.RUNS/RUN/'install/state.json'
        original=a.read(path)
        for change in ({'outcome':'terminal_uncertainty_no_commands'},{'cleanup':'unverified'},
                       {'code_sha256':'drift'},{'write_dispatches':[{'source':'candidate'},{'source':'stock'}]},
                       {'captures':[]}):
            a.durable(path,{**state,**change})
            with self.subTest(change=change),self.assertRaises(b.Refused):a.check_install(RUN,a.code_receipt()['sha256'],getattr(self,'install_token',None))
        path.write_bytes(original)
        capture=a.RUNS/RUN/'install'/state['captures'][-1]['file'];capture.write_bytes(self.stock)
        with self.assertRaises(b.Refused):a.check_install(RUN,a.code_receipt()['sha256'],getattr(self,'install_token',None))

    def test_restore_pin_topology_change_refused(self):
        self.invoke('pin-install');self.invoke('install')
        self.fake.row['usb']='2-9'
        path=self.directory/'restore-contract.json';c=contract('pin-restore');c['install_completion_token']=self.install_token;a.durable(path,c)
        with patch.object(subprocess,'run',side_effect=self.fake),patch.object(b,'EXECUTE_LOCK',self.directory/'lock'):
            self.assertEqual(self.cli(['pin-restore','--execute','--run-id',RUN,'--contract',str(path),
                                       '--supervised','--physical-fallback-present'])[0],2)
        self.assertFalse(any(w['source']=='stock' for w in self.fake.inner.writes))

    def test_no_override_cli_options(self):
        with contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit):a.parser().parse_args(['install','--image','arbitrary'])
        for forbidden in ('connect','tcpip','reboot','fastboot'):
            self.assertNotIn(forbidden,a.parser().format_help())

    def test_original_sources_and_artifacts_unchanged(self):
        before=a.json_file(a.ROOT/'evidence/original-inputs.before.json')
        for name,expected in before.items():
            self.assertEqual(a.sha(a.read(a.WORKSPACE/name)),expected,name)

    def test_future_or_missing_monotonic_pin_refused(self):
        for change in ({'schema':1}, {'created_monotonic':None},
                       {'created_monotonic':float('nan')},
                       {'created_monotonic':time.monotonic()+10}):
            p=pin();p.update(change)
            with self.subTest(change=change),self.assertRaises(b.Refused):
                a.validate_pin(p,RUN,a.code_receipt()['sha256'])

    def test_host_boot_epoch_change_refuses_pin(self):
        p=pin()
        with patch.object(a,'host_clock_epoch',return_value='darwin:11111111-1111-4111-8111-111111111111'):
            with self.assertRaises(b.Refused):a.validate_pin(p,RUN,a.code_receipt()['sha256'])

    def test_wall_rollback_does_not_extend_monotonic_pin(self):
        clock={'wall':2000000000.0,'mono':1000.0}
        with patch.object(time,'time',side_effect=lambda:clock['wall']),patch.object(time,'monotonic',side_effect=lambda:clock['mono']):
            p=pin();c=contract('install');c['valid_until']=clock['wall']+590
            g=a.Guard(c,RUN,'install',a.code_receipt()['sha256'],p)
            self.assertEqual(g.end_mono,1180)
            clock.update(wall=2000000100.0,mono=1200.0)
            with self.assertRaises(b.UncertainTransport):g.check()
            self.assertTrue(g.stopped)

    def test_late_loaded_pin_caps_existing_contract_guard(self):
        clock={'wall':2000000000.0,'mono':1000.0}
        with patch.object(time,'time',side_effect=lambda:clock['wall']),patch.object(time,'monotonic',side_effect=lambda:clock['mono']):
            p=pin();clock.update(wall=2000000100.0,mono=1100.0)
            c=contract('install');c['valid_until']=clock['wall']+590
            g=a.Guard(c,RUN,'install',a.code_receipt()['sha256'])
            g.pin=p;g.check()
            self.assertEqual(g.end_mono,1180)
            clock.update(wall=2000000101.0,mono=1180.0)
            with self.assertRaises(b.UncertainTransport):g.check()

    def test_current_pin_epoch_is_stable_and_serializable(self):
        p=pin()
        self.assertEqual(p['host_clock_epoch'],a.host_clock_epoch())
        self.assertEqual(json.loads(json.dumps(p))['created_monotonic'],p['created_monotonic'])
        a.validate_pin(p,RUN,a.code_receipt()['sha256'])


    def test_remote_alias_and_geometry_fail_before_any_write(self):
        for mutation in ('alias','start','size','dev','sector'):
            directory=self.directory/'boundary'
            if directory.exists():
                import shutil;shutil.rmtree(directory)
            t=self.make_transport();self.fake=Fake(self.stock)
            if mutation=='alias':self.fake.inner.alias='/dev/block/mmcblk0p9'
            else:
                key={'start':'/sys/class/block/mmcblk0p10/start','size':'/sys/class/block/mmcblk0p10/size',
                     'dev':'/sys/class/block/mmcblk0p10/dev','sector':'/sys/class/block/mmcblk0/queue/logical_block_size'}[mutation]
                self.fake.inner.sysfs[key]='999'
            with patch.object(subprocess,'run',side_effect=self.fake),self.assertRaises(b.OperationFailed):t.setup()
            self.assertFalse(self.fake.inner.writes)

    def test_actual_candidate_boundary_expiry_preserves_known_stock_status(self):
        t=self.make_transport()
        t.journal.observed(self.stock)
        original=a.durable
        def expire(path,value):
            original(path,value)
            if value.get('stdin') and 'dd if='+t.vault+'/candidate.bin of='+b.BLOCK in value['stdin']:
                t.guard.pin['created_at']=time.time()-181
        with patch.object(a,'durable',side_effect=expire),patch.object(subprocess,'run',side_effect=self.fake),self.assertRaises(b.UncertainTransport):t.write('candidate')
        self.assertFalse(self.fake.inner.writes)
        self.assertEqual(t.journal.state['partition_status'],'exact_stock')
        self.assertFalse(t.journal.state['partition_may_be_modified'])
        self.assertEqual(t.journal.state['write_dispatches'][0]['delivery'],'not_dispatched_run_consumed')
        count=len(self.fake.calls)
        with self.assertRaises(b.UncertainTransport):t.write('stock')
        self.assertEqual(count,len(self.fake.calls))

    def test_timeout_partial_stderr_and_aggregate_helper_error_preserved(self):
        t=self.make_transport();self.fake.stderr='completed staging stderr\n'
        self.fake.root_exception=subprocess.TimeoutExpired(['fixture'],75,output=b'partial output',stderr=b'partial stderr')
        with patch.object(subprocess,'run',side_effect=self.fake),self.assertRaises(b.UncertainTransport) as caught:t.setup()
        self.assertIn('completed staging stderr',str(caught.exception))
        records=[a.json_file(p) for p in t.directory.glob('*-uncertain.json')]
        self.assertTrue(any(r['partial_stderr_hex']==b'partial stderr'.hex() for r in records))

    def test_shared_lock_contention_refuses_before_transport(self):
        path=self.directory/'contract.json';a.durable(path,contract('pin-install'))
        lock=self.directory/'lock';lock.touch()
        with patch.object(b,'EXECUTE_LOCK',lock),a.mutation_lock(),patch.object(subprocess,'run',side_effect=self.fake):
            code,_,_=self.cli(['pin-install','--execute','--run-id',RUN,'--contract',str(path),
                              '--supervised','--physical-fallback-present'])
        self.assertEqual(code,2);self.assertFalse(self.fake.calls)

    def test_absent_supervision_or_fallback_flag_refuses_before_transport(self):
        path=self.directory/'contract.json';a.durable(path,contract('pin-install'))
        for flags in ([],['--supervised'],['--physical-fallback-present']):
            with patch.object(subprocess,'run',side_effect=self.fake):
                code,_,_=self.cli(['pin-install','--execute','--run-id',RUN,'--contract',str(path),*flags])
            self.assertEqual(code,2);self.assertFalse(self.fake.calls)

    def test_local_reviewed_source_and_helper_drift_refused(self):
        original=a.read
        for leaf in ('adapter.py','root_shell_wifi.py','mtk-su-mirror-b'):
            def changed(path,maximum=20_000_000):
                data=original(path,maximum)
                return data+b'changed' if Path(path).name==leaf else data
            with self.subTest(leaf=leaf),patch.object(a,'read',side_effect=changed),self.assertRaises(b.Refused):a.check_sources()

    def test_restore_already_original_requires_clean_install_linkage(self):
        self.fake.inner.block=self.stock
        with self.assertRaises((ValueError,b.Refused)):a.check_install(RUN,a.code_receipt()['sha256'],getattr(self,'install_token',None))
        self.invoke('pin-install');self.invoke('install')
        # Models stock autorepair or a separately parent-owned exact return; makes no boot claim.
        self.fake.inner.block=self.stock;self.fake.row['transport_id']='24'
        self.invoke('pin-restore');state=self.invoke('restore')
        self.assertEqual(state['outcome'],'verified_already_original')
        self.assertEqual([w['source'] for w in self.fake.inner.writes],['candidate'])

    def test_copy_of_stock_backup_not_accepted_as_capture(self):
        state,t=self.run_engine()
        capture=state['captures'][-1]
        capture['root_completion']['sha256']='0'*64
        with self.assertRaises(b.Refused):a.verify_capture(t.directory,state,a.FULL_SHA)

    def test_monotonic_deadline_cannot_be_extended_by_wall_clock(self):
        t=self.make_transport();t.guard.end_mono=time.monotonic()-1
        with patch.object(subprocess,'run',side_effect=self.fake),self.assertRaises(b.UncertainTransport):t.usb_enumeration()
        self.assertFalse(self.fake.calls)


    def test_dependency_has_no_standalone_writer_cli(self):
        with self.assertRaises(SystemExit) as caught:
            exec(compile(a.read(a.ROOT/'source/engine.py'),'dependency-only','exec'),{'__name__':'__main__'})
        self.assertIn('Dependency only',str(caught.exception))


    def test_restore_cannot_reconstruct_live_completion_from_visible_journal(self):
        self.invoke('pin-install');self.invoke('install')
        state,_=a.check_install(RUN,a.code_receipt()['sha256'],self.install_token)
        self.assertEqual(a.sha(self.install_token.encode()),state['live_completion_token_sha256'])
        self.assertNotIn(self.install_token,a.read(a.RUNS/RUN/'install/state.json').decode())
        for receipt in (None,'0'*64,state['live_completion_token_sha256']):
            with self.assertRaises(b.Refused):a.check_install(RUN,a.code_receipt()['sha256'],receipt)

    def test_deadline_rechecked_after_local_source_verification(self):
        t=self.make_transport();original=a.check_sources
        def slow():
            original();t.guard.end_mono=time.monotonic()-1
        with patch.object(a,'check_sources',side_effect=slow),patch.object(subprocess,'run',side_effect=self.fake),self.assertRaises(b.UncertainTransport):t.usb_enumeration()
        self.assertFalse(self.fake.calls)

    def test_lost_final_publication_cannot_authorize_later_restore(self):
        self.invoke('pin-install')
        path=self.directory/'install-contract.json';a.durable(path,contract('install'))
        original=a.durable;tripped=[]
        def loss(path,value):
            if tripped:raise OSError('fixture storage unavailable after lost publication')
            original(path,value)
            if 'live_completion_token_sha256' in value:
                tripped.append(len(self.fake.calls))
                raise OSError('fixture directory fsync failure after rename')
        with patch.object(a,'durable',side_effect=loss),patch.object(subprocess,'run',side_effect=self.fake),patch.object(b,'EXECUTE_LOCK',self.directory/'lock'):
            code,out,err=self.cli(['install','--execute','--run-id',RUN,'--contract',str(path),
                                  '--supervised','--physical-fallback-present'])
        self.assertEqual(code,2);self.assertNotIn('install_completion_token',out)
        visible=a.json_file(a.RUNS/RUN/'install/state.json')
        self.assertEqual(visible['outcome'],'installed_full_hash_verified')
        self.assertIn('live_completion_token_sha256',visible)
        self.assertEqual(len(self.fake.calls),tripped[0])
        with self.assertRaises(b.Refused):a.check_install(RUN,a.code_receipt()['sha256'],None)

    def test_candidate_full_staging_mismatch_prevents_candidate_dispatch(self):
        t=self.make_transport()
        def corrupt_candidate(argv,script):
            if script and 'cp '+t.inbox+'/input.bin '+t.vault+'/candidate.bin' in script:
                self.fake.inner.fault='staging_corruption'
        self.fake.before=corrupt_candidate
        with patch.object(subprocess,'run',side_effect=self.fake):state=a.execute('install',self.stock,self.full,t,t.journal)
        self.assertEqual(state['outcome'],'refused_or_failed_stop')
        self.assertFalse(self.fake.inner.writes)
        self.assertFalse(t.journal.state['write_dispatches'])

    def prior_failed_full(self):
        image = a.read(a.WORKSPACE/'2026-11-06-asus-stock-only-ram-rescue-build/artifacts/candidate/UNAPPROVED-STOCK-ONLY.img')
        data = image + bytes(b.SIZE-len(image))
        self.assertEqual(a.sha(data),a.PRIOR_FAILED_SHA)
        return data

    def test_direct_prior_failed_preimage_install_and_linkage(self):
        self.fake.inner.block=self.prior_failed_full()
        self.invoke('pin-install');state=self.invoke('install')
        self.assertEqual(state['install_preimage_sha256'],a.PRIOR_FAILED_SHA)
        self.assertEqual(state['install_preimage_bytes'],b.SIZE)
        self.assertEqual([w['source'] for w in self.fake.inner.writes],['candidate'])
        linked,_=a.check_install(RUN,a.code_receipt()['sha256'],self.install_token)
        self.assertEqual(linked['captures'][0]['sha256'],a.PRIOR_FAILED_SHA)
        self.assertEqual(linked['captures'][-1]['sha256'],a.FULL_SHA)
        self.assertFalse(linked['probe_report_observed'])

    def test_original_preimage_record_and_tampered_preimage_linkage_refused(self):
        self.invoke('pin-install');state=self.invoke('install')
        self.assertEqual(state['install_preimage_sha256'],b.STOCK_HASH)
        self.assertEqual(state['install_preimage_bytes'],b.SIZE)
        path=a.RUNS/RUN/'install/state.json'
        for change in ({'install_preimage_sha256':a.PRIOR_FAILED_SHA},
                       {'install_preimage_sha256':'0'*64}, {'install_preimage_sha256':None},
                       {'install_preimage_bytes':b.SIZE-1}):
            a.durable(path,{**state,**change})
            with self.subTest(change=change),self.assertRaises(b.Refused):
                a.check_install(RUN,a.code_receipt()['sha256'],self.install_token)

    def test_unexpected_complete_preimage_rejected_without_dispatch(self):
        unexpected=bytearray(self.prior_failed_full());unexpected[-1]^=1
        state,t=self.run_engine(initial=bytes(unexpected))
        self.assertEqual(state['outcome'],'refused_or_failed_stop')
        self.assertFalse(self.fake.inner.writes)
        self.assertFalse(state['write_dispatches'])
        self.assertNotIn('install_preimage_sha256',state)

    def test_prior_failed_known_candidate_failure_uses_only_fixed_original_inverse(self):
        state,t=self.run_engine('partial',initial=self.prior_failed_full())
        self.assertEqual(state['outcome'],'install_failed_fixed_inverse_verified')
        self.assertEqual(state['install_preimage_sha256'],a.PRIOR_FAILED_SHA)
        self.assertEqual([w['source'] for w in self.fake.inner.writes],['candidate','stock'])
        self.assertEqual(a.sha(self.fake.inner.block),b.STOCK_HASH)
        self.assertTrue(state['restore_verified'])

    def test_prior_failed_uncertain_completion_no_inverse_or_later_commands(self):
        state,t=self.run_engine('lost_write',initial=self.prior_failed_full())
        self.assertEqual(state['outcome'],'terminal_uncertainty_no_commands')
        self.assertEqual([w['source'] for w in self.fake.inner.writes],['candidate'])
        count=len(self.fake.calls)
        with self.assertRaises(b.UncertainTransport):t.write('stock')
        self.assertEqual(len(self.fake.calls),count)

    def test_exact_minimal_probe_identity_and_source_scope(self):
        p=a.json_file(a.ROOT/'profile.json')
        self.assertEqual(p['profile'],'asus-p00a-minimal-readonly-ramusb-recovery-deployment-v1')
        self.assertEqual(p['target_capabilities'],['stock_kernel_minimal_PID1_tmpfs_readonly_RAMUSB_discriminator_only'])
        self.assertEqual(p['image']['bytes'],7759872)
        self.assertEqual(p['p10']['allowed_install_preimage_sha256'],list(a.INSTALL_PREIMAGES))
        self.assertEqual(a.IMAGE,a.WORKSPACE/'2026-11-06-asus-minimal-ram-usb-probe/artifacts/candidate.img')
        self.assertFalse(p['automatic_return_proven']);self.assertFalse(p['physical_GO'])
        for name in ('engine.py','root_dispatch.py'):
            self.assertEqual(a.read(a.ROOT/'source'/name),a.read(a.WORKSPACE/'2026-11-06-asus-rescue-pin-monotonic-fix/source'/name))
