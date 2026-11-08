"""Offline only. No test launches adb, the root helper, or a device command."""
import copy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SPIKE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('recovery_control', SPIKE / 'source/recovery_control.py')
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)
OBSERVATIONS = []


def candidate_fixture(stock):
    """Deliberately nonbootable synthetic ramdisk mutation, NEVER a reviewed control."""
    parsed = c.unpack_image(stock)
    b = bytearray(stock[:parsed['end']])
    offset = 2048 + ((len(parsed['kernel']) + 2047) // 2048) * 2048
    b[offset + 512] ^= 1
    return bytes(b)


def manifest_for(image):
    padded = image + bytes(c.SIZE - len(image))
    return dict(schema_version=1, profile=c.PROFILE, target=c.TARGET.copy(),
                candidate=dict(path='synthetic-DO-NOT-INSTALL.bin', bytes=len(image), sha256=c.sha(image),
                               wrapped_kernel_sha256=c.KERNEL_HASH, header_page_sha256=c.sha(image[:2048])),
                padding=dict(kind='constant-byte', byte=0, full_partition_sha256=c.sha(padded)),
                review=dict(approved=True, reviewer='OFFLINE TEST FIXTURE ONLY',
                            reference='not reviewed for hardware; never execute', marker='synthetic-test',
                            bounded_return_seconds=60, ram_only_no_persistent_mounts_or_writes=True,
                            manual_recovery_and_normal_boot=True))


class FakeAdbRoot:
    """Models remote files/block bytes and observable dd attempts, not the engine."""
    def __init__(self, stock, action='install', fault=None):
        self.block = stock
        self.files = {}
        self.calls = []
        self.root_scripts = []
        self.writes = []
        self.fault = fault
        self.action = action
        self.session = c.BASE + '/' + action
        self.props = dict([('ro.serialno', c.SERIAL), ('ro.product.device', 'P00A_2'),
                           ('ro.build.version.sdk', '24'), ('ro.build.fingerprint', c.FINGERPRINT),
                           ('sys.boot_completed', '1'), ('ro.adb.secure', '1')])
        self.serial = c.ENDPOINT
        self.sysfs = {
            '/sys/class/block/mmcblk0p10/partition': '10',
            '/sys/class/block/mmcblk0p10/start': '160184',
            '/sys/class/block/mmcblk0p10/size': '32696',
            '/sys/class/block/mmcblk0p10/dev': '179:10',
            '/sys/class/block/mmcblk0/queue/logical_block_size': '512',
        }
        self.alias = c.BLOCK
        self.selinux = 'Enforcing'
        self.lost_at = None
        self.candidate_written = False
        self.restore_written = False
        self.stage_exists = False

    def __call__(self, argv, *, input=None, **kwargs):
        self.calls.append(list(argv))
        if argv[:3] == ['adb', '-s', c.ENDPOINT]:
            args = argv[3:]
            if args == ['get-serialno']:
                return subprocess.CompletedProcess(argv, 0, self.serial + '\n', '')
            if args[:2] == ['shell', 'getprop']:
                return subprocess.CompletedProcess(argv, 0, self.props[args[2]] + '\n', '')
            if args == ['shell', 'getenforce']:
                return subprocess.CompletedProcess(argv, 0, self.selinux + '\n', '')
            if args[0] == 'push':
                assert args[2] == self.session + '/inbox/input.bin'
                self.files[args[2]] = Path(args[1]).read_bytes()
                return subprocess.CompletedProcess(argv, 0, 'pushed\n', '')
            if args[0] == 'pull':
                assert args[1] == self.session + '/inbox/readback.bin'
                Path(args[2]).write_bytes(self.files[args[1]])
                return subprocess.CompletedProcess(argv, 0, 'pulled\n', '')
            raise AssertionError('Unexpected ADB call: ' + repr(args))
        assert argv == [sys.executable, str(c.HELPER)], argv
        self.root_scripts.append(input)
        assert c.DEVICE_GUARD in input, 'Root guard missing'
        token = re.search(r'ASUS_RECOVERY_RC_([0-9a-f]{32})=', input).group(1)
        status, helper_status = 0, 0
        comparisons = re.findall(r'\[ "\$\(cat ([^ )]+)\)" = ([^ ]+) \]', input)
        assert len(comparisons) == 5
        geometry_ok = all(self.sysfs[path] == value for path, value in comparisons)
        alias_expected = re.search(r'\[ "\$\(readlink -f ' + re.escape(c.ALIAS) + r'\)" = ([^ ]+) \]', input).group(1)
        if not geometry_ok or self.alias != alias_expected:
            status = 1
        elif 'mkdir ' + self.session + '\n' in input:
            status = 1 if self.stage_exists else 0
            self.stage_exists = True
        elif re.search(r'dd if=\S+ of=' + re.escape(c.BLOCK) + ' ', input):
            match = re.search(r'dd if=(\S+) of=(\S+) bs=(\d+) count=(\d+)\n', input)
            assert match is not None, 'Unbounded write'
            source, target, bs, count = match.groups()
            assert int(bs) * int(count) == c.SIZE
            assert target == c.BLOCK
            kind = Path(source).stem
            assert kind in ('candidate', 'stock')
            payload = self.files[source]
            self.writes.append(dict(source=kind, target=target, bytes=len(payload), sha256=c.sha(payload)))
            if kind == 'candidate':
                self.candidate_written = True
                if self.fault == 'denied':
                    status = 13
                elif self.fault in ('partial', 'lost_write', 'inverse_failure', 'unhealthy_after_failure'):
                    self.block = payload[:c.SIZE // 2] + self.block[c.SIZE // 2:]
                    status = 5
                    if self.fault == 'unhealthy_after_failure':
                        self.props['sys.boot_completed'] = '0'
                    if self.fault == 'lost_write':
                        self.lost_at = len(self.calls)
                        raise subprocess.TimeoutExpired(argv, 95)
                elif self.fault == 'mismatch':
                    self.block = payload[:-1] + bytes([payload[-1] ^ 1])
                else:
                    self.block = payload
            else:
                self.restore_written = True
                if self.fault in ('inverse_failure', 'restore_failure'):
                    self.block = payload[:1024] + self.block[1024:]
                    status = 9
                elif self.fault == 'restore_mismatch':
                    self.block = payload[:-1] + bytes([payload[-1] ^ 1])
                else:
                    self.block = payload
        elif f'dd if={c.BLOCK} ' in input:
            if self.candidate_written and self.fault == 'lost_readback':
                self.lost_at = len(self.calls)
                raise subprocess.TimeoutExpired(argv, 95)
            if self.candidate_written and not self.restore_written and self.fault == 'read_error':
                status = 6
            else:
                self.files[self.session + '/inbox/readback.bin'] = self.block
        elif 'cp ' + self.session + '/inbox/input.bin ' in input:
            dest = re.search(r'cp \S+/inbox/input.bin (\S+)', input).group(1)
            self.files[dest] = self.files[self.session + '/inbox/input.bin']
            self.files[self.session + '/inbox/readback.bin'] = self.files[dest]
            if self.fault == 'staging_corruption':
                self.files[self.session + '/inbox/readback.bin'] = bytes(c.SIZE)
        elif 'rmdir ' + self.session + '\n' in input:
            if self.fault == 'cleanup':
                status = 7
            self.stage_exists = False
        else:
            raise AssertionError('Unexpected root script')
        stdout = f'root wrapper noise\nASUS_RECOVERY_RC_{token}={status}\n'
        if self.fault == 'helper_failed' and self.candidate_written:
            helper_status = 1
        if self.fault == 'missing_status' and self.candidate_written:
            stdout = 'lost completion record\n'
        return subprocess.CompletedProcess(argv, helper_status, stdout, '')


class OfflineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stock, cls.records = c.local_inputs()
        cls.image = candidate_fixture(cls.stock)
        cls.full = cls.image + bytes(c.SIZE - len(cls.image))

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='offline-', dir=SPIKE / 'tests')
        self.directory = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def scenario(self, name, *, action='install', fault=None, configure=None):
        fake = FakeAdbRoot(self.stock, action, fault)
        if configure:
            configure(fake)
        journal = c.Journal(self.directory, action, 'FAKE_EXECUTE_OFFLINE')
        transport = c.AdbRootTransport(self.directory, journal, action)
        with patch.object(c.subprocess, 'run', side_effect=fake):
            state = c.execute(action, self.stock, self.full if action == 'install' else None, transport, journal)
        OBSERVATIONS.append(dict(case=name, outcome=state['outcome'],
                                 writes=fake.writes, restore_verified=state['restore_verified'],
                                 manual_recovery_permitted=state['manual_recovery_permitted'],
                                 cleanup=state.get('cleanup'), final_full_sha256=c.sha(fake.block),
                                 commands_after_loss=None if fake.lost_at is None else len(fake.calls) - fake.lost_at,
                                 root_statuses=[dict(operation=e['operation'], exit_status=e['exit_status'],
                                                     helper_exit_status=e['helper_exit_status'])
                                                for e in state['events'] if e['kind'] == 'root_status']))
        return fake, state

    def assert_writes(self, fake, kinds):
        self.assertEqual([w['source'] for w in fake.writes], kinds)
        self.assertEqual({w['target'] for w in fake.writes}, {c.BLOCK} if kinds else set())
        self.assertTrue(all(w['bytes'] == c.SIZE for w in fake.writes))

    def test_install_success(self):
        fake, state = self.scenario('install_success')
        self.assert_writes(fake, ['candidate'])
        self.assertEqual(fake.block, self.full)
        self.assertEqual(state['outcome'], 'installed_full_hash_verified')
        self.assertTrue(state['manual_recovery_permitted'])
        self.assertFalse(state['restore_verified'])

    def test_restore_changed(self):
        fake, state = self.scenario('exact_restore', action='restore', configure=lambda f: setattr(f, 'block', self.full))
        self.assert_writes(fake, ['stock'])
        self.assertEqual(fake.block, self.stock)
        self.assertTrue(state['restore_verified'])
        self.assertEqual(state['outcome'], 'restored_full_hash_verified')

    def test_restore_already_stock(self):
        fake, state = self.scenario('automatic_stock_repair_already_restored', action='restore')
        self.assert_writes(fake, [])
        self.assertTrue(state['restore_verified'])
        self.assertEqual(state['outcome'], 'verified_already_restored')

    def test_wrong_serial(self):
        fake, state = self.scenario('wrong_serial', configure=lambda f: setattr(f, 'serial', 'OTHER'))
        self.assert_writes(fake, [])
        self.assertEqual(state['outcome'], 'refused_before_write')

    def test_wrong_os(self):
        fake, state = self.scenario('wrong_fingerprint', configure=lambda f: f.props.update({'ro.build.fingerprint': 'OTHER'}))
        self.assert_writes(fake, [])
        self.assertEqual(state['outcome'], 'refused_before_write')

    def test_wrong_size(self):
        for suffix, wrong in (('mmcblk0p10/size', '32695'), ('mmcblk0p10/start', '160185'),
                              ('mmcblk0p10/dev', '179:9'), ('mmcblk0p10/partition', '9'),
                              ('mmcblk0/queue/logical_block_size', '4096')):
            fake, state = self.scenario('wrong_geometry_' + suffix,
                                        configure=lambda f: f.sysfs.update({'/sys/class/block/' + suffix: wrong}))
            self.assert_writes(fake, [])
            self.assertEqual(state['outcome'], 'refused_before_write')

    def test_wrong_alias(self):
        fake, state = self.scenario('wrong_by_name_alias', configure=lambda f: setattr(f, 'alias', '/dev/block/mmcblk0p9'))
        self.assert_writes(fake, [])
        self.assertEqual(state['outcome'], 'refused_before_write')

    def test_wrong_current_hash(self):
        fake, state = self.scenario('wrong_current_recovery_hash', configure=lambda f: setattr(f, 'block', self.full))
        self.assert_writes(fake, [])
        self.assertEqual(state['outcome'], 'refused_before_write')

    def test_staging_corruption(self):
        fake, state = self.scenario('staged_input_corruption', fault='staging_corruption')
        self.assert_writes(fake, [])
        self.assertEqual(state['outcome'], 'refused_before_write')

    def test_partial_write_inverse(self):
        fake, state = self.scenario('partial_write_exit_5_stock_inverse', fault='partial')
        self.assert_writes(fake, ['candidate', 'stock'])
        self.assertEqual(fake.block, self.stock)
        self.assertTrue(state['restore_verified'])
        self.assertFalse(state['manual_recovery_permitted'])
        self.assertEqual(state['outcome'], 'install_failed_stock_inverse_verified')
        self.assertTrue(any(e.get('exit_status') == 5 and e.get('helper_exit_status') == 0 for e in state['events']))

    def test_denied_write_stock_unchanged(self):
        fake, state = self.scenario('write_denied_stock_unchanged', fault='denied')
        self.assert_writes(fake, ['candidate'])
        self.assertEqual(fake.block, self.stock)
        self.assertEqual(state['outcome'], 'install_failed_verified_already_restored')
        self.assertTrue(state['restore_verified'])
        self.assertFalse(state['manual_recovery_permitted'])

    def test_mismatch_inverse(self):
        fake, state = self.scenario('successful_write_wrong_full_hash', fault='mismatch')
        self.assert_writes(fake, ['candidate', 'stock'])
        self.assertEqual(fake.block, self.stock)
        self.assertTrue(state['restore_verified'])
        self.assertEqual(state['outcome'], 'install_failed_stock_inverse_verified')

    def test_known_read_error_still_attempts_inverse(self):
        fake, state = self.scenario('read_error_healthy_android_stock_inverse', fault='read_error')
        self.assert_writes(fake, ['candidate', 'stock'])
        self.assertEqual(fake.block, self.stock)
        self.assertEqual(state['outcome'], 'install_failed_stock_inverse_verified')
        self.assertTrue(state['restore_verified'])

    def test_generated_shell_syntax_without_execution(self):
        scripts = []
        for action in ('install', 'restore'):
            fake, _ = self.scenario('shell_syntax_' + action, action=action,
                                    configure=None if action == 'install' else lambda f: setattr(f, 'block', self.full))
            scripts.extend(fake.root_scripts)
        for script in scripts:
            parsed = subprocess.run(['/bin/sh', '-n'], input=script, text=True, capture_output=True, timeout=5)
            self.assertEqual(parsed.returncode, 0, parsed.stderr)
            destinations = re.findall(r'dd if=\S+ of=(\S+)', script)
            for destination in destinations:
                self.assertIn(destination, (c.BLOCK, c.BASE + '/install/vault/readback.bin',
                                            c.BASE + '/restore/vault/readback.bin'))
            self.assertNotRegex(script, r'\b(reboot|fastboot|mount|umount|flash_image)\b')

    def test_lost_transport(self):
        for fault in ('lost_write', 'lost_readback', 'helper_failed', 'missing_status'):
            with self.subTest(fault=fault):
                fake, state = self.scenario(fault, fault=fault)
                self.assert_writes(fake, ['candidate'])
                self.assertEqual(state['outcome'], 'transport_uncertain_no_retry')
                self.assertFalse(state['restore_verified'])
                self.assertFalse(state['manual_recovery_permitted'])
                if fake.lost_at:
                    self.assertEqual(len(fake.calls), fake.lost_at)

    def test_unhealthy_android_no_inverse(self):
        fake, state = self.scenario('boot_incomplete_after_partial_write', fault='unhealthy_after_failure')
        self.assert_writes(fake, ['candidate'])
        self.assertEqual(state['outcome'], 'inverse_unverified_stop')
        self.assertFalse(state['restore_verified'])

    def test_inverse_fails_no_retry(self):
        fake, state = self.scenario('inverse_write_failure', fault='inverse_failure')
        self.assert_writes(fake, ['candidate', 'stock'])
        self.assertEqual(state['outcome'], 'inverse_unverified_stop')
        self.assertFalse(state['restore_verified'])

    def test_restore_failure_no_retry(self):
        for fault in ('restore_failure', 'restore_mismatch'):
            with self.subTest(fault=fault):
                fake, state = self.scenario(fault, action='restore', fault=fault,
                                            configure=lambda f: setattr(f, 'block', self.full))
                self.assert_writes(fake, ['stock'])
                self.assertEqual(state['outcome'], 'restore_unverified_stop')
                self.assertFalse(state['restore_verified'])

    def test_cleanup_cannot_authorize_recovery(self):
        fake, state = self.scenario('cleanup_failure_after_verified_install', fault='cleanup')
        self.assert_writes(fake, ['candidate'])
        self.assertEqual(state['outcome'], 'installed_full_hash_verified')
        self.assertEqual(state['cleanup'], 'unverified')
        self.assertFalse(state['manual_recovery_permitted'])

    def test_existing_stage_refused(self):
        fake, state = self.scenario('preexisting_staging_refused', configure=lambda f: setattr(f, 'stage_exists', True))
        self.assert_writes(fake, [])
        self.assertEqual(state['outcome'], 'refused_before_write')

    def test_android7_numeric_device_guard(self):
        cases = [
            ('correct', 'brw-r----- 1 0 1000 179,  10 2026-11-05 23:54 /dev/block/mmcblk0p10', True),
            ('wrong_major', 'brw-r----- 1 0 1000 178,  10 2026-11-05 23:54 /dev/block/mmcblk0p10', False),
            ('wrong_minor', 'brw-r----- 1 0 1000 179,  9 2026-11-05 23:54 /dev/block/mmcblk0p10', False),
            ('wrong_node', 'brw-r----- 1 0 1000 179,  10 2026-11-05 23:54 /dev/block/mmcblk0p9', False),
            ('missing', '', False),
        ]
        for name, listing, expected in cases:
            with self.subTest(name=name):
                # ls is a local mock function; this never accesses /dev.
                script = "set -eu\nls() { printf '%s\\n' '" + listing + "'; }\n" + c.NODE_RDEV_GUARD
                result = subprocess.run(['/bin/sh', '-c', script], text=True, capture_output=True)
                self.assertEqual(result.returncode == 0, expected)

    def test_root_status_real_local_shell(self):
        token = 'a' * 32
        # Replace ALL device guards with ':' before executing a local /bin/sh.
        # Body contains only a subshell exit and a printf; never a device command.
        script = c.root_envelope('(exit 23)\nprintf SHOULD_NOT_RUN', token).replace(c.DEVICE_GUARD, ':')
        result = subprocess.run(['/bin/sh'], input=script, text=True, capture_output=True, timeout=5)
        self.assertEqual(result.returncode, 0)
        self.assertNotIn('SHOULD_NOT_RUN', result.stdout)
        self.assertEqual(c.root_status(result, token), 23)
        OBSERVATIONS.append(dict(case='real_local_shell_failed_operation_cleanup_success',
                                 operation_exit_status=23, outer_exit_status=result.returncode, device_contacted=False))

    def test_status_parser_rejects_ambiguous_or_helper_error(self):
        token = 'a' * 32
        for rc, stdout in ((0, ''), (0, f'ASUS_RECOVERY_RC_{token}=0\n' * 2),
                           (1, f'ASUS_RECOVERY_RC_{token}=0\n')):
            with self.assertRaises(c.UncertainTransport):
                c.root_status(subprocess.CompletedProcess([], rc, stdout, ''), token)

    def write_manifest(self, m):
        path = self.directory / 'manifest.json'
        path.write_text(json.dumps(m))
        return path, c.sha(path.read_bytes())

    def test_manifest_valid_and_mutations(self):
        (self.directory / 'synthetic-DO-NOT-INSTALL.bin').write_bytes(self.image)
        valid = manifest_for(self.image)
        path, digest = self.write_manifest(valid)
        actual, _ = c.validate_candidate(path, digest, self.stock)
        self.assertEqual(actual, self.full)
        cases = [
            ('wrong_target', lambda m: m['target'].update(block='/dev/block/mmcblk0p9')),
            ('missing_review', lambda m: m['review'].update(approved=False)),
            ('candidate_hash', lambda m: m['candidate'].update(sha256='0' * 64)),
            ('padding_hash', lambda m: m['padding'].update(full_partition_sha256='0' * 64)),
            ('padding_byte', lambda m: m['padding'].update(byte=256)),
            ('kernel_hash', lambda m: m['candidate'].update(wrapped_kernel_sha256='0' * 64)),
        ]
        for name, mutate in cases:
            m = copy.deepcopy(valid)
            mutate(m)
            path, digest = self.write_manifest(m)
            with self.assertRaises(c.Refused, msg=name):
                c.validate_candidate(path, digest, self.stock)
        path, digest = self.write_manifest(valid)
        with self.assertRaises(c.Refused):
            c.validate_candidate(path, '0' * 64, self.stock)
        # A rehashed modified kernel must still fail byte comparison to the immutable stock source.
        modified = bytearray(self.image)
        modified[2048 + 600] ^= 1
        (self.directory / 'synthetic-DO-NOT-INSTALL.bin').write_bytes(modified)
        path, digest = self.write_manifest(manifest_for(bytes(modified)))
        with self.assertRaisesRegex(c.Refused, 'exact stock kernel'):
            c.validate_candidate(path, digest, self.stock)
        OBSERVATIONS.append(dict(case='manifest_mutations', rejected=[name for name, _ in cases] + ['reviewed_manifest_hash', 'rehash_changed_kernel'], device_contacted=False))

    def test_wrong_backup_refuses_offline(self):
        bad = self.directory / 'wrong-recovery.bin'
        bad.write_bytes(bytes(c.SIZE))
        with patch.object(c, 'BACKUPS', (bad, c.BACKUPS[1])):
            with self.assertRaisesRegex(c.Refused, 'Stock backup mismatch'):
                c.local_inputs()

    def test_default_plan_never_launches_subprocess(self):
        (self.directory / 'synthetic-DO-NOT-INSTALL.bin').write_bytes(self.image)
        path, digest = self.write_manifest(manifest_for(self.image))
        run = self.directory / 'plan'
        run.mkdir()
        with patch.object(c, 'new_run', return_value=run), patch.object(c.subprocess, 'run', side_effect=AssertionError('Plan contacted transport')) as process, patch('sys.stdout', new_callable=io.StringIO):
            result = c.main(['install', '--manifest', str(path), '--reviewed-manifest-sha256', digest])
        self.assertEqual(result, 0)
        process.assert_not_called()
        state = json.loads((run / 'state.json').read_text())
        self.assertFalse(state['device_contacted'])
        self.assertEqual(state['write_dispatches'], [])
        OBSERVATIONS.append(dict(case='default_plan', outcome=state['outcome'], subprocess_calls=0, device_contacted=False))

    def test_execute_without_supervision_never_launches_subprocess(self):
        run = self.directory / 'refused'
        run.mkdir()
        with patch.object(c, 'new_run', return_value=run), patch.object(c.subprocess, 'run', side_effect=AssertionError('Invalid invocation contacted transport')) as process, patch('sys.stderr', new_callable=io.StringIO):
            result = c.main(['restore', '--execute'])
        self.assertEqual(result, 2)
        process.assert_not_called()

    def test_endpoint_does_not_replace_hardware_identity(self):
        for wrong in ('OTHER', c.ENDPOINT, ''):
            fake, state = self.scenario('wrong_hardware_' + wrong,
                configure=lambda f, value=wrong: f.props.update({'ro.serialno': value}))
            self.assert_writes(fake, [])
            self.assertEqual(state['outcome'], 'refused_before_write')
            self.assertEqual(fake.root_scripts, [])

    def test_insecure_or_missing_adb_is_refused_before_root(self):
        for wrong in ('0', ''):
            fake, state = self.scenario('insecure_adb_' + wrong,
                configure=lambda f, value=wrong: f.props.update({'ro.adb.secure': value}))
            self.assert_writes(fake, [])
            self.assertEqual(state['outcome'], 'refused_before_write')
            self.assertEqual(fake.root_scripts, [])

    def test_hardware_serial_is_not_an_accepted_network_endpoint(self):
        fake, state = self.scenario('hardware_used_as_endpoint',
                                   configure=lambda f: setattr(f, 'serial', c.SERIAL))
        self.assert_writes(fake, [])
        self.assertEqual(state['outcome'], 'refused_before_write')
        self.assertEqual(fake.root_scripts, [])

    def test_all_adb_calls_use_fixed_wifi_endpoint_and_journal_records_it(self):
        fake, state = self.scenario('wifi_exact_endpoint_success')
        self.assertEqual(state['transport'], c.TRANSPORT)
        self.assertEqual(state['target']['serial'], c.SERIAL)
        for argv in fake.calls:
            if argv[0] == 'adb':
                self.assertEqual(argv[:3], ['adb', '-s', c.ENDPOINT])
        self.assertNotEqual(c.ENDPOINT, c.SERIAL)
        self.assertIn('[ "$(getprop ro.adb.secure)" = 1 ]', c.DEVICE_GUARD)

    def test_no_endpoint_or_partition_override_or_retry_interface(self):
        for option in ('--endpoint', '--serial', '--target', '--retry', '--resume'):
            with patch.object(c.subprocess, 'run', side_effect=AssertionError('transport forbidden')), \
                 patch('sys.stderr', new_callable=io.StringIO), self.assertRaises(SystemExit):
                c.main(['restore', option, 'OTHER'])

    def test_changed_pinned_wifi_helper_refused_before_transport(self):
        bad = self.directory / 'changed-helper.py'
        bad.write_text('raise SystemExit(0)')
        with patch.object(c, 'HELPER', bad), \
             patch.object(c.subprocess, 'run', side_effect=AssertionError('transport forbidden')):
            with self.assertRaisesRegex(c.Refused, 'Pinned root dependency changed'):
                c.local_inputs()



if __name__ == '__main__':
    os.umask(0o077)
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(OfflineTests)
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    text = stream.getvalue()
    print(text, end='')
    (SPIKE / 'evidence/offline-tests.txt').write_text(text)
    c.write_json(SPIKE / 'evidence/offline-tests.json', dict(
        device_contacted=False, transport='fake ADB and fake root helper; one local /bin/sh status test with device guards removed',
        tests_run=result.testsRun, failures=len(result.failures), errors=len(result.errors),
        scenarios=OBSERVATIONS))
    raise SystemExit(0 if result.wasSuccessful() else 1)
