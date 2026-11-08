"""All transport calls are emulated. No ADB, helper, USB or device command runs."""
import copy
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

p = load('probe_transport', ROOT / 'source/probe_transport.py')
b, o = p.b, p.o
legacy = load('legacy_tests', ROOT / 'tests/legacy_fakes.py')
legacy.c = b
observer_tests = load('observer_tests', ROOT / 'tests/observer_fixtures.py')
observer_tests.o = o
RUN = '142cf5d3-b649-4334-90a5-d71b6137ff65'
STOCK_ROW = dict(serial=b.SERIAL, state='device', usb='17895424X', product='WW_P00A',
                 model='P00A', device='P00A_2', transport_id='17')
OBSERVATIONS = []


def pin(**changes):
    return {**dict(schema=1, run_id=RUN, profile=o.PROFILE, candidate_sha256=o.IMAGE_SHA,
                   padded_sha256=o.PADDED_SHA, created_at=time.time(), observer_sha256=p.OBSERVER_SHA,
                   stock=copy.deepcopy(STOCK_ROW), properties=copy.deepcopy(o.PROPS), enforcing=True), **changes}


class Fake(legacy.FakeAdbRoot):
    def __init__(self, stock, action='install', fault=None):
        super().__init__(stock, action, fault)
        self.session = b.BASE + '/' + RUN + '-' + action
        self.row = copy.deepcopy(STOCK_ROW)
        self.usb_fault = None
        self.last_label = None

    def __call__(self, argv, *, input=None, **kwargs):
        if argv[:2] == ['adb', 'devices']:
            self.calls.append(list(argv))
            if self.usb_fault == 'lost' and self.candidate_written:
                self.lost_at = len(self.calls)
                raise subprocess.TimeoutExpired(argv, 12)
            row = dict(self.row)
            if self.usb_fault == 'changed' and self.candidate_written:
                row['transport_id'] = '99'
                self.lost_at = len(self.calls)
            line = row['serial'] + ' ' + row['state'] + ' ' + ' '.join(k + ':' + v for k, v in row.items() if k not in ('serial', 'state'))
            wifi = b.ENDPOINT + ' device product:WW_P00A model:P00A device:P00A_2 transport_id:31'
            return subprocess.CompletedProcess(argv, 0, 'List of devices attached\n' + line + '\n' + wifi + '\n', '')
        if argv[:3] == ['adb', '-t', self.row['transport_id']]:
            self.calls.append(list(argv))
            if argv[3:] == ['shell', 'getenforce']:
                value = self.selinux
            else:
                assert argv[3:5] == ['shell', 'getprop']
                value = self.props[argv[5]]
            return subprocess.CompletedProcess(argv, 0, value + '\n', '')
        if input:
            self.last_label = 'partition' if f'dd if={b.BLOCK} ' in input else 'stage'
        result = super().__call__(argv, input=input, **kwargs)
        if argv[:3] == ['adb', '-s', b.ENDPOINT] and argv[3] == 'pull' and self.fault == 'short_read' and self.last_label == 'partition':
            Path(argv[-1]).write_bytes(b'partial')
        return result


class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stock, cls.full, cls.local = p.verify_local()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=ROOT / 'tests')
        self.directory = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
        # Any accidentally unmocked process creation fails before reaching an executable.
        self.addCleanup(patch.stopall)
        patch.object(subprocess, 'Popen', side_effect=AssertionError('Actual process forbidden')).start()
        patch.object(subprocess, 'check_output', side_effect=AssertionError('Actual process forbidden')).start()
        patch.object(subprocess, 'run', side_effect=AssertionError('Actual process forbidden')).start()

    def scenario(self, action='install', fault=None, configure=None, before=None):
        directory = self.directory / str(len(list(self.directory.iterdir())))
        directory.mkdir()
        fake = Fake(self.stock if before is None else before, action, fault)
        if configure:
            configure(fake)
        current_pin = pin()
        journal = p.Journal(directory, action, RUN, current_pin, {}, mode='FAKE_EXECUTE_OFFLINE')
        transport = p.Transport(directory, journal, action, current_pin, RUN)
        with patch.object(subprocess, 'run', side_effect=fake):
            state = p.run_readback(transport, journal) if action == 'readback' else b.execute(action, self.stock, self.full if action == 'install' else None, transport, journal)
        OBSERVATIONS.append(dict(action=action, fault=fault, outcome=state['outcome'],
                                 writes=[x['source'] for x in fake.writes],
                                 final_sha256=b.sha(fake.block), device_contacted=False,
                                 commands_after_loss=None if fake.lost_at is None else len(fake.calls)-fake.lost_at))
        return fake, state, directory

    def test_frozen_components_and_profile(self):
        self.assertEqual(b.sha(self.full), o.PADDED_SHA)
        self.assertEqual(self.local['profile']['kernel']['input_sha256'], p.KERNEL_SHA)
        self.assertFalse(self.local['profile']['physical_execution_authorized'])

    def test_wrong_candidate_kernel_and_profile(self):
        wrong = self.directory / 'wrong'; wrong.write_bytes(b'wrong')
        for module, key in [(o, 'IMAGE'), (p, 'KERNEL'), (p, 'PROFILE_FILE')]:
            with self.subTest(key=key), patch.object(module, key, wrong), self.assertRaises(b.Refused):
                p.verify_local()

    def test_stock_only_guard_still_rejects_real_frozen_candidate(self):
        image = o.IMAGE.read_bytes()
        (self.directory / 'synthetic-DO-NOT-INSTALL.bin').write_bytes(image)
        manifest = legacy.manifest_for(image)
        path = self.directory / 'manifest.json'; path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(b.Refused, 'exact stock kernel'):
            b.validate_candidate(path, b.sha(path.read_bytes()), self.stock)

    def test_install_full_readback_and_no_mode_authority(self):
        fake, state, _ = self.scenario()
        self.assertEqual(state['outcome'], 'installed_full_hash_verified')
        self.assertEqual([w['source'] for w in fake.writes], ['candidate'])
        self.assertEqual(fake.block, self.full)
        self.assertEqual(state['captures'][-1]['sha256'], o.PADDED_SHA)
        self.assertFalse(state['manual_recovery_permitted'])
        self.assertFalse(state['hardware_ready'])
        for argv in fake.calls:
            if argv[0] == 'adb' and argv[1] == '-s':
                self.assertEqual(argv[2], b.ENDPOINT)
        for script in fake.root_scripts:
            self.assertIn(b.DEVICE_GUARD, script)
            self.assertNotRegex(script, r'\b(reboot|mount|umount|fastboot)\b')
            self.assertNotIn('of=/dev/block/mmcblk0p9', script)

    def test_known_failed_write_exactly_one_inverse(self):
        for fault in ('partial', 'mismatch', 'read_error'):
            with self.subTest(fault=fault):
                fake, state, _ = self.scenario(fault=fault)
                self.assertEqual([w['source'] for w in fake.writes], ['candidate', 'stock'])
                self.assertEqual(fake.block, self.stock)
                self.assertEqual(state['outcome'], 'install_failed_stock_inverse_verified')

    def test_denied_write_idempotent_inverse(self):
        fake, state, _ = self.scenario(fault='denied')
        self.assertEqual([w['source'] for w in fake.writes], ['candidate'])
        self.assertEqual(state['outcome'], 'install_failed_verified_already_restored')

    def test_inverse_failure_no_second_attempt(self):
        fake, state, _ = self.scenario(fault='inverse_failure')
        self.assertEqual([w['source'] for w in fake.writes], ['candidate', 'stock'])
        self.assertEqual(state['outcome'], 'inverse_unverified_stop')

    def test_restore_and_idempotent_restore(self):
        for before, expected in [(self.full, ['stock']), (self.stock, [])]:
            fake, state, _ = self.scenario(action='restore', before=before)
            self.assertEqual([w['source'] for w in fake.writes], expected)
            self.assertTrue(state['restore_verified'])
            self.assertEqual(state['captures'][-1]['sha256'], b.STOCK_HASH)

    def test_restore_failure_no_retry(self):
        for fault in ('restore_failure', 'restore_mismatch'):
            fake, state, _ = self.scenario(action='restore', before=self.full, fault=fault)
            self.assertEqual([w['source'] for w in fake.writes], ['stock'])
            self.assertEqual(state['outcome'], 'restore_unverified_stop')

    def test_readback_never_writes_or_stages_inputs(self):
        fake, state, _ = self.scenario(action='readback')
        self.assertEqual(state['outcome'], 'stock_readback_verified')
        self.assertFalse(fake.writes)
        self.assertFalse(any('push' in c for c in fake.calls))
        self.assertEqual(len(state['captures']), 1)
        fake, state, _ = self.scenario(action='readback', before=self.full)
        self.assertEqual(state['outcome'], 'readback_unverified_stop')
        self.assertFalse(fake.writes)

    def test_uncertain_wifi_zero_followup_commands(self):
        for fault in ('lost_write', 'lost_readback', 'helper_failed', 'missing_status'):
            fake, state, _ = self.scenario(fault=fault)
            self.assertEqual(state['outcome'], 'transport_uncertain_no_retry')
            self.assertEqual([w['source'] for w in fake.writes], ['candidate'])
            if fake.lost_at:
                self.assertEqual(fake.lost_at, len(fake.calls))
            self.assertNotEqual(state.get('cleanup'), 'verified')

    def test_uncertain_usb_zero_followup_commands(self):
        for fault in ('lost', 'changed'):
            fake, state, _ = self.scenario(configure=lambda f: setattr(f, 'usb_fault', fault))
            self.assertEqual(state['outcome'], 'transport_uncertain_no_retry')
            self.assertEqual(fake.lost_at, len(fake.calls))
            self.assertEqual([w['source'] for w in fake.writes], ['candidate'])

    def test_wrong_identity_and_secure_adb_and_enforcing(self):
        for key, value in [('ro.serialno', 'OTHER'), ('ro.adb.secure', '0'), ('ro.build.fingerprint', 'OTHER')]:
            fake, state, _ = self.scenario(configure=lambda f: f.props.update({key:value}))
            self.assertFalse(fake.writes)
            self.assertFalse(fake.root_scripts)
        fake, state, _ = self.scenario(configure=lambda f: setattr(f, 'selinux', 'Permissive'))
        self.assertFalse(fake.root_scripts)

    def test_wrong_usb_identity(self):
        for key, value in [('usb', 'different'), ('serial', 'wrong'), ('transport_id', '18'), ('model', 'wrong')]:
            fake, state, _ = self.scenario(configure=lambda f: f.row.update({key:value}))
            self.assertFalse(fake.root_scripts)
            self.assertFalse(fake.writes)

    def test_all_geometry_guards(self):
        for key in Fake(self.stock).sysfs:
            fake, state, _ = self.scenario(configure=lambda f: f.sysfs.update({key:'WRONG'}))
            self.assertFalse(fake.writes)
            self.assertEqual(state['outcome'], 'refused_before_write')
        fake, state, _ = self.scenario(configure=lambda f: setattr(f, 'alias', '/dev/block/mmcblk0p9'))
        self.assertFalse(fake.writes)

    def test_staging_corruption_and_short_read(self):
        for fault in ('staging_corruption', 'short_read'):
            fake, state, _ = self.scenario(fault=fault)
            self.assertFalse(fake.writes)
            self.assertEqual(state['outcome'], 'refused_before_write')

    def test_existing_stage_and_wrong_current_partition(self):
        fake, state, _ = self.scenario(configure=lambda f: setattr(f, 'stage_exists', True))
        self.assertFalse(fake.writes)
        fake, state, _ = self.scenario(before=self.full)
        self.assertFalse(fake.writes)

    def test_stale_pin_wrong_run_profile_observer_and_model(self):
        for delta in [dict(created_at=time.time()-181), dict(created_at=time.time()+5), dict(run_id='other'),
                      dict(profile='stock'), dict(observer_sha256='wrong'), dict(enforcing=False),
                      dict(stock={**STOCK_ROW,'model':'other'})]:
            with self.subTest(delta=delta), self.assertRaises((o.Refused,b.Refused)):
                p.validate_pin(pin(**delta), RUN)

    def cli(self, args):
        with patch('sys.stdout', new_callable=io.StringIO) as stdout, patch('sys.stderr', new_callable=io.StringIO) as stderr:
            result = p.main(args)
        return result, stdout.getvalue(), stderr.getvalue()

    def test_default_plan_all_actions_no_transport(self):
        for action in ('plan','verify-local','install','restore','readback','finalize'):
            result, output, _ = self.cli([action])
            self.assertEqual(result,0)
            self.assertEqual(json.loads(output)['mode'],'PLAN_ONLY')
            self.assertFalse(json.loads(output)['device_contacted'])

    def test_execution_missing_attestations_and_hashes(self):
        for flags in [[],['--parent-reviewed'],['--parent-reviewed','--supervised'],
                      ['--parent-reviewed','--supervised','--physical-fallback-present']]:
            self.assertEqual(self.cli(['install','--execute',*flags])[0],2)

    def test_no_override_or_retry_interface(self):
        for flag in ('--endpoint','--target','--image','--retry','--resume','--serial'):
            with patch('sys.stderr',new_callable=io.StringIO),self.assertRaises(SystemExit):
                p.main(['install',flag,'other'])

    def test_shared_lock_contention_before_contact(self):
        path=self.directory/'lock'
        with patch.object(b,'EXECUTE_LOCK',path), p.mutation_lock():
            with self.assertRaises(BlockingIOError):
                with p.mutation_lock():
                    self.fail('Lock did not exclude competitor')

    def test_reservation_never_resumes(self):
        with patch.object(p,'RUNS',self.directory/'runs'):
            p.reserve(RUN,'install')
            with self.assertRaises(FileExistsError): p.reserve(RUN,'install')

    def lifecycle(self):
        runs=self.directory/'runs'
        patch.object(p,'RUNS',runs).start()
        patch.object(b,'EXECUTE_LOCK',self.directory/'lock').start()
        pinfile=self.directory/'pin.json'; b.write_json(pinfile,pin())
        args=['--execute','--run-id',RUN,'--pin',str(pinfile),'--parent-reviewed','--supervised',
              '--physical-fallback-present','--reviewed-profile-sha256',p.PROFILE_SHA,
              '--reviewed-code-sha256',p.code_receipt()['sha256']]
        install_fake=Fake(self.stock)
        with patch.object(subprocess,'run',side_effect=install_fake):
            code,_,err=self.cli(['install',*args]); self.assertEqual(code,0,err)
        installpath=runs/RUN/'install/state.json'; install=p.json_file(installpath)
        obsdir=self.directory/'observe'; obsdir.mkdir()
        report=observer_tests.report()
        observation=o.observe(observer_tests.FakeAdb(report),install['pin'],RUN,obsdir,sleep=lambda _:None)
        obspath=obsdir/'observation.json'; b.write_json(obspath,observation)
        self.assertFalse(observation['stock_recovery_readback_verified'])
        self.assertTrue(observation['stock_returned'])
        # New exact stock preflight after return: same physical topology, new current transport ID.
        current=pin(stock={**STOCK_ROW,'transport_id':'19'})
        b.write_json(pinfile,current)
        restore_fake=Fake(self.full,'restore'); restore_fake.row=current['stock']
        with patch.object(subprocess,'run',side_effect=restore_fake):
            code,_,err=self.cli(['restore',*args]); self.assertEqual(code,0,err)
        readerpath=runs/RUN/'restore/state.json'
        return args, install, observation, obspath, readerpath, current

    def test_complete_emulated_lifecycle_and_finalization(self):
        args,install,observation,obspath,readerpath,current=self.lifecycle()
        final_fake=Fake(self.stock,'finalize'); final_fake.row=current['stock']
        with patch.object(subprocess,'run',side_effect=final_fake):
            code,_,err=self.cli(['finalize',*args,'--observation',str(obspath),'--reader-journal',str(readerpath)])
            self.assertEqual(code,0,err)
        acceptance=p.json_file(p.RUNS/RUN/'finalize/acceptance.json')
        self.assertTrue(acceptance['overall_accepted'])
        self.assertTrue(acceptance['stock_recovery_readback_verified'])
        self.assertFalse(acceptance['hardware_ready'])
        self.assertFalse(final_fake.writes)

    def test_finalizer_refuses_copied_backup_and_journal_tampering(self):
        args,install,observation,obspath,readerpath,current=self.lifecycle()
        original=p.json_file(readerpath)
        readback,_=p.capture_for_finalize(readerpath,RUN,install,observation)
        self.assertEqual(b.sha(readback.read_bytes()),b.STOCK_HASH)
        cases=[('mode',lambda s:s.update(mode='PLAN_ONLY')),
               ('run',lambda s:s.update(run_id='other')),
               ('profile',lambda s:s.update(profile='stock')),
               ('before_return',lambda s:s.update(started_at=observation['returned_at']-1)),
               ('no_capture',lambda s:s.update(captures=[])),
               ('backup_as_capture',lambda s:s['captures'][-1].update(file='copied-backup.bin')),
               ('wrong_root_receipt',lambda s:s['captures'][-1].update(root_command_sha256='wrong'))]
        (readerpath.parent/'copied-backup.bin').write_bytes(self.stock)
        for name,mutate in cases:
            state=copy.deepcopy(original); mutate(state); b.write_json(readerpath,state)
            with self.subTest(name=name),self.assertRaises(b.Refused):
                p.capture_for_finalize(readerpath,RUN,install,observation)
        b.write_json(readerpath,original)
        readback.write_bytes(b'partial')
        with self.assertRaises(b.Refused): p.capture_for_finalize(readerpath,RUN,install,observation)

    def test_pin_expiry_during_staging_prevents_candidate_write(self):
        directory = self.directory / 'expired'; directory.mkdir()
        current = pin()
        journal = p.Journal(directory, 'install', RUN, current, {}, mode='FAKE_EXECUTE_OFFLINE')
        transport = p.Transport(directory, journal, 'install', current, RUN)
        fake = Fake(self.stock)
        original_stage = transport.stage
        def stage(kind, data):
            original_stage(kind, data)
            if kind == 'candidate':
                current['created_at'] = time.time() - 181
        with patch.object(transport, 'stage', side_effect=stage), patch.object(subprocess, 'run', side_effect=fake):
            state = b.execute('install', self.stock, self.full, transport, journal)
        self.assertFalse(fake.writes)
        self.assertEqual(state['outcome'], 'install_failed_verified_already_restored')

    def test_prior_uncertain_restore_blocks_followup(self):
        with patch.object(p, 'RUNS', self.directory / 'runs'):
            directory = p.reserve(RUN, 'restore')
            for state in [{}, dict(outcome='restore_unverified_stop'),
                          dict(outcome='restored_full_hash_verified', cleanup='unverified')]:
                b.write_json(directory / 'state.json', state)
                with self.assertRaises(b.Refused): p.prior_restore_guard(RUN)
            b.write_json(directory / 'state.json', dict(outcome='verified_already_restored',
                         cleanup='verified', restore_verified=True))
            p.prior_restore_guard(RUN)

    def test_changed_root_helper_refused_offline(self):
        changed = self.directory / 'helper'; changed.write_text('changed')
        with patch.object(b, 'HELPER', changed), self.assertRaises(b.Refused): p.verify_local()

    def test_lock_contention_at_cli_never_contacts_transport(self):
        pinfile = self.directory / 'pin.json'; b.write_json(pinfile, pin())
        args = ['install', '--execute', '--run-id', RUN, '--pin', str(pinfile), '--parent-reviewed',
                '--supervised', '--physical-fallback-present', '--reviewed-profile-sha256', p.PROFILE_SHA,
                '--reviewed-code-sha256', p.code_receipt()['sha256']]
        with patch.object(b, 'EXECUTE_LOCK', self.directory / 'lock'), p.mutation_lock():
            self.assertEqual(self.cli(args)[0], 2)

    def test_same_run_reservation_blocks_second_cli_install(self):
        args, install, observation, obspath, readerpath, current = self.lifecycle()
        self.assertEqual(self.cli(['install', *args])[0], 2)

    def test_invalid_observation_never_finalizes_from_stock_return_alone(self):
        args, install, observation, obspath, readerpath, current = self.lifecycle()
        # Use the actual journal-linked capture, then exercise the unchanged observer gates.
        readback, _ = p.capture_for_finalize(readerpath, RUN, install, observation)
        for changes in [dict(run_id='other'), dict(pin_sha256='wrong'), dict(stock_returned=False),
                        dict(status='FAILED_OR_INCOMPLETE'), dict(observer_error='transport lost')]:
            with self.subTest(changes=changes), self.assertRaises(o.Refused):
                o.finalize(observer_tests.FakeAdb(observer_tests.report()), install['pin'], RUN,
                           {**observation, **changes}, obspath.parent, readback)

    def test_failed_or_uncertain_install_cannot_restore_again(self):
        with patch.object(p,'RUNS',self.directory/'runs'):
            directory=p.reserve(RUN,'install')
            state=dict(mode='EXECUTE',run_id=RUN,profile=o.PROFILE,candidate_sha256=o.IMAGE_SHA,
                       profile_sha256=p.PROFILE_SHA,code_sha256=p.code_receipt()['sha256'],cleanup='verified')
            for outcome in ('transport_uncertain_no_retry','inverse_unverified_stop','install_failed_stock_inverse_verified'):
                b.write_json(directory/'state.json',{**state,'outcome':outcome})
                with self.assertRaises(b.Refused): p.check_install(RUN,p.code_receipt()['sha256'])


if __name__=='__main__':
    os.umask(0o077)
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    b.write_json(ROOT/'evidence/offline-tests.json',dict(tests_run=result.testsRun,failures=len(result.failures),
                 errors=len(result.errors),device_contacted=False,actual_subprocess_calls=0,
                 scope='Emulated USB inventory, Wi-Fi files, guarded root scripts and p10 block bytes; no hardware proof',scenarios=OBSERVATIONS))
    raise SystemExit(0 if result.wasSuccessful() else 1)
