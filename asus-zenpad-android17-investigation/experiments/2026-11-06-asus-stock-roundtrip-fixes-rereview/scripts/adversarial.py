"""Offline adversarial review. All subprocess/network effects are blocked or mocked."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import re
import subprocess
import sys
import unittest
from unittest.mock import patch

R = Path(__file__).resolve().parents[1]
P = R.parent / '2026-11-06-asus-stock-roundtrip-parent-fixes'
sys.dont_write_bytecode = True
sys.path.insert(0, str(P / 'source/service'))
import controller as C

spec = importlib.util.spec_from_file_location('fixtures', R / 'tests/service/test_faults.py')
M = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = M
spec.loader.exec_module(M)  # Installs the original process/network audit denial hook.
T, F, E = M.T, M.F, M.E
RECORDS = []


class ReviewChecks(M.Base):
    def test_entry_shape_matrix_and_integrated_whitespace_escape(self):
        cases = [
            (0, b'', b'', 'completion_unconfirmed'),
            (1, b'', b'error: closed\n', 'unknown'),
            (-9, b'', b'', 'unknown'),
            (0, b'\n', b'', 'unknown'),
            (1, b'reboot failed: -1\n', b'', 'explicit_service_failure'),
            (1, b'reboot failed: -1\r\n', b'', 'explicit_service_failure'),
            (-9, b'reboot failed: -1\n', b'', 'unknown'),
            (1, b'reboot failed: -1\n', b'closed', 'unknown'),
            (1, b'reboot failed: -1\nreboot failed: -1\n', b'', 'unknown'),
            (1, b' \t\nreboot failed: -1\n\n\x0b', b'', 'explicit_service_failure'),
            (1, b'\xc2\xa0reboot failed: -1\xc2\xa0', b'', 'explicit_service_failure'),
        ]
        for i, (rc, out, err, observed) in enumerate(cases):
            host = T.HostIO(self.root / ('shape-' + str(i)))
            host.authorization_check = lambda: None
            with patch.object(T.subprocess, 'run', return_value=subprocess.CompletedProcess([], rc, out, err)):
                result = host.entry({'initial_transport_id': '1'})
            self.assertEqual(result['delivery'], observed)
            RECORDS.append(dict(case='entry_shape', rc=rc, stdout_hex=out.hex(), stderr_hex=err.hex(),
                                delivery=result['delivery']))

        def entry(host, pin):
            host.entries += 1
            adapter = T.HostIO(self.root / 'integrated-adapter')
            adapter.authorization_check = host.authorization_check
            with patch.object(T.subprocess, 'run', return_value=subprocess.CompletedProcess(
                    [], 1, b' \t\nreboot failed: -1\n\n\x0b', b'')):
                return adapter.entry(pin)
        with patch.object(M.FakeHost, 'entry', entry):
            dev, host, result = self.trial()
        self.assertEqual(host.tcp, 1)
        self.assertEqual(dev.writes, ['candidate', 'stock'])
        RECORDS.append(dict(case='unexpected_entry_shape_after_newstock', tcp_calls=host.tcp,
                            writes=dev.writes, outcome=result['outcome'], delivery=result['entry_delivery']))

    def test_nested_root_helper_starts_commands_after_expiry(self):
        helper = type(sys)('review_pinned_helper')
        helper.__file__ = str(E.HELPER)
        source = E.HELPER.read_bytes()
        self.assertEqual(F.sha(source), E.HELPER_HASH)
        exec(compile(source, str(E.HELPER), 'exec'), helper.__dict__)
        expired = [False]
        checks = []
        nested = []
        host = T.HostIO(self.root / 'commands')
        journal = C.Journal(self.root, 'install', 'OFFLINE_FIXTURE')
        transport = T.Transport(self.root, journal, 'install', M.RUN, 'install', M.OLD, host)
        def authorize():
            checks.append(expired[0])
            if expired[0]:
                raise F.AuthorizationExpired('fixture expiry before next nested dispatch')
        transport.authorization_check = authorize

        def query(argv, **kwargs):
            nested.append(dict(kind='query', argv=argv, after_expiry=expired[0]))
            if argv[-1] == 'get-serialno':
                return F.ENDPOINT
            if argv[-1] == 'getenforce':
                return 'Enforcing'
            return helper.PROPS[argv[-1]]

        def process(argv, **kwargs):
            if argv[0] == sys.executable and argv[1] == str(E.HELPER):
                self.assertFalse(expired[0])
                output, error = io.StringIO(), io.StringIO()
                with patch.object(sys, 'stdin', io.StringIO(kwargs['input'])), \
                        contextlib.redirect_stdout(output), contextlib.redirect_stderr(error):
                    rc = helper.main()
                return subprocess.CompletedProcess(argv, rc, output.getvalue(), error.getvalue())
            item = dict(kind='run', argv=argv, after_expiry=expired[0])
            nested.append(item)
            if argv[-2] == 'shell' and 'stat -c' in argv[-1]:
                expired[0] = True  # The helper precheck completed; no root/write request yet.
            script = kwargs.get('input', '')
            if script:
                item['contains_p10_write'] = bool(re.search(r'dd if=\S+ of=/dev/block/mmcblk0p10 ', script))
                (R / 'evidence/generated-write-helper-script.sh').write_text(script)
                op = re.search(r'ASUS_RECOVERY_RC_([0-9a-f]{32})=', script).group(1)
                wifi = re.search(r'ASUS_WIFI_ROOT_([0-9a-f]{32})=', script).group(1)
                return subprocess.CompletedProcess(argv, 0,
                    f'\nASUS_RECOVERY_RC_{op}=0\n\nASUS_WIFI_ROOT_{wifi}=0\n', '')
            return subprocess.CompletedProcess(argv, 0, '', '')

        with patch.object(T.subprocess, 'run', side_effect=process), \
                patch.object(T.subprocess, 'check_output', side_effect=query), \
                patch.object(E, 'SIZE', 16740352):
            transport.write('candidate')
        post = [x for x in nested if x['after_expiry']]
        self.assertTrue(any(x.get('contains_p10_write') for x in post))
        self.assertEqual(checks, [False, False])
        RECORDS.append(dict(case='nested_helper_expiry_gap', checks=checks, commands=nested,
                            after_expiry_count=len(post), root_status=journal.state['events'][-1]))

    def test_nonexpiry_preentry_inverse_exceptions_omit_modified_state(self):
        for i, kind in enumerate(('uncertain', 'refused', 'failed')):
            old = self.root
            self.root = old / str(i)
            self.root.mkdir()
            dev, host, result = self.trial(behavior='not_ready', fault='restore-guard:snapshot', kind=kind)
            self.assertEqual(dev.writes, ['candidate'])
            self.assertEqual(host.entries, 0)
            self.assertNotIn('partition_may_be_modified', result)
            self.assertEqual(result['outcome'], 'preentry_refused_inverse_unverified_stop')
            RECORDS.append(dict(case='preentry_inverse_exception', exception_kind=kind,
                                writes=dev.writes, entry_calls=host.entries,
                                partition_may_be_modified=result.get('partition_may_be_modified', 'ABSENT'),
                                p10_restored=result['p10_restored'], outcome=result['outcome'],
                                install_outcome=result['install_result']['outcome']))
            self.root = old

    def test_expiry_does_not_inherit_inverse_exceptions(self):
        for kind in (E.Refused, E.OperationFailed, E.UncertainTransport, E.VerificationFailed, OSError):
            self.assertFalse(issubclass(F.AuthorizationExpired, kind))

    def test_real_transport_and_entry_stop_after_intent_before_outer_dispatch(self):
        for name in ('setup', 'candidate', 'stock', 'staging_push', 'cleanup', 'guard_cleanup', 'entry'):
            directory = self.root / name
            directory.mkdir()
            host = T.HostIO(directory / 'commands')
            journal = C.Journal(directory, 'install', 'OFFLINE_FIXTURE')
            transport = T.Transport(directory, journal, 'install', M.RUN, 'install', M.OLD, host)
            expired = [False]
            durable = F.durable
            def save(path, *args, **kwargs):
                result = durable(path, *args, **kwargs)
                if path.parent == host.directory and path.name == '0001.json':
                    expired[0] = True
                return result
            def check():
                if expired[0]:
                    raise F.AuthorizationExpired('fixture expired during durable command intent')
            host.authorization_check = transport.authorization_check = check
            transport.stage_created = True
            if name == 'guard_cleanup':
                transport.extra.add('para.bin')
            operations = dict(setup=transport.setup, candidate=lambda: transport.write('candidate'),
                              stock=lambda: transport.write('stock'),
                              staging_push=lambda: transport.stage('candidate', M.CANDIDATE),
                              cleanup=transport.cleanup, guard_cleanup=transport.cleanup,
                              entry=lambda: host.entry({'initial_transport_id': '1'}))
            with patch.object(F, 'durable', side_effect=save), patch.object(T.subprocess, 'run') as process:
                with self.assertRaises(F.AuthorizationExpired):
                    operations[name]()
                process.assert_not_called()
            completion = json.loads((host.directory / '0001-result.json').read_text())
            self.assertEqual(completion['status'], 'authorization_expired_before_dispatch')
            RECORDS.append(dict(case='outer_dispatch_after_intent', operation=name, subprocess_calls=0,
                                status=completion['status']))

    def test_every_fixture_writer_boundary_stops_following_calls_on_expiry(self):
        # Additional phase-level sweep. The root-helper test above covers the real nested hole.
        dev, host, result = self.trial()
        sequence = list(dev.calls)
        old = self.root
        points = [(label, sum(x == label for x in sequence[:i + 1]))
                  for i, label in enumerate(sequence) if not label.startswith(('host:', 'observer:'))]
        for i, (label, occurrence) in enumerate(points):
            self.root = old / ('boundary-' + str(i))
            self.root.mkdir()
            expired = [False]
            real = M.Device.step
            def step(device, current):
                result = real(device, current)
                if current == label and device.counts[current] == occurrence:
                    expired[0] = True
                return result
            def check():
                if expired[0]:
                    raise F.AuthorizationExpired('fixture boundary expiry')
            with patch.object(M.Device, 'step', step):
                d, h, r = self.trial(recheck=check)
            # Final snapshot completion has no following command, so completed evidence may succeed.
            self.assertEqual(d.calls, sequence[:len(d.calls)])
            expired_at = next(n for n in range(1, len(sequence) + 1)
                if sequence[n - 1] == label and sequence[:n].count(label) == occurrence)
            # Independently bounded read-only pin/observer work is intentionally not an inverse.
            self.assertTrue(all(x.startswith(('host:inventory', 'host:snapshot', 'observer:start'))
                                for x in d.calls[expired_at:]), d.calls[expired_at:])
            RECORDS.append(dict(case='writer_phase_expiry', boundary=label, occurrence=occurrence,
                                outcome=r['outcome'], writes=d.writes,
                                stock_readback_retained=r['p10_restored']))
            self.root = old


if __name__ == '__main__':
    with (R / 'evidence/adversarial.txt').open('w') as stream:
        result = unittest.TextTestRunner(stream=stream, verbosity=2).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(ReviewChecks))
    receipt = dict(tests=result.testsRun, failures=len(result.failures), errors=len(result.errors),
                   passed=result.wasSuccessful(), records=RECORDS, device_contacted=False,
                   meaning='Passing defect reproductions assert observed defects, not safety compliance.')
    (R / 'evidence/adversarial.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({k: v for k, v in receipt.items() if k != 'records'}))
    raise SystemExit(not result.wasSuccessful())
