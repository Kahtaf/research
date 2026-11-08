"""Concrete independent-review regressions; no external/device execution."""
import datetime as dt
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('review_fix_fixtures', HERE / 'test_faults.py')
M = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = M
spec.loader.exec_module(M)
C, T, F = M.C, M.T, M.F


class ReviewRegressions(M.Base):
    def test_entry_errors_observe_but_never_enable_tcp_or_inverse(self):
        cases = [(1, b'', b'error: closed\n'), (-9, b'', b''),
                 (0, b'unexpected\n', b''), (0, b'', b'unexpected\n')]
        for i, (rc, out, err) in enumerate(cases):
            old = self.root
            self.root = old / str(i)
            self.root.mkdir()

            def entry(host, pin):
                host.entries += 1
                host.dev.step('host:entry')
                adapter = T.HostIO(self.root / 'adapter')
                adapter.authorization_check = host.authorization_check
                with patch.object(adapter, 'command', return_value=subprocess.CompletedProcess([], rc, out, err)):
                    return adapter.entry(pin)

            with patch.object(M.FakeHost, 'entry', entry):
                dev, host, result = self.trial()
            self.assertEqual(result['entry_delivery']['delivery'], 'unknown')
            self.assertTrue(result['stock_returned'])
            self.assertEqual(host.tcp, 0)
            self.assertEqual(dev.writes, ['candidate'])
            self.assertEqual(result['outcome'], 'entry_transport_uncertain_observed_no_mutation_stop')
            self.root = old

    def test_clean_completion_and_exact_service_failure_keep_new_boot_gate(self):
        for i, (rc, out, delivery) in enumerate([(0, b'', 'completion_unconfirmed'),
                                               (1, b'reboot failed: -1\n', 'explicit_service_failure')]):
            host = T.HostIO(self.root / str(i))
            host.authorization_check = lambda: None
            with patch.object(host, 'command', return_value=subprocess.CompletedProcess([], rc, out, b'')):
                self.assertEqual(host.entry({'initial_transport_id': '1'})['delivery'], delivery)

    def test_expiry_at_all_three_reviewed_writer_boundaries(self):
        cases = [('install:stage_candidate', None, []),
                 ('install:write_candidate', 'install:write_candidate', ['candidate']),
                 ('restore:stage_stock', None, ['candidate'])]
        for i, (boundary, fault, expected) in enumerate(cases):
            old = self.root
            self.root = old / str(i)
            self.root.mkdir()
            expired = [False]
            real = M.Device.step

            def step(dev, label):
                if label == boundary:
                    expired[0] = True
                return real(dev, label)

            def check():
                if expired[0]:
                    raise F.AuthorizationExpired('fixture expired')

            with patch.object(M.Device, 'step', step):
                dev, host, result = self.trial(fault=fault, kind='failed' if fault else 'uncertain', recheck=check)
            self.assertEqual(dev.writes, expected)
            self.assertEqual(result['outcome'], 'authorization_expired_no_new_command')
            self.assertFalse(result['metadata_reverified'])
            self.root = old

    def test_expiry_after_command_intent_prevents_actual_dispatch(self):
        host = T.HostIO(self.root / 'commands')
        expired = [False]
        durable = F.durable

        def save(path, *args, **kwargs):
            result = durable(path, *args, **kwargs)
            if path.name == '0001.json':
                expired[0] = True
            return result

        def check():
            if expired[0]:
                raise F.AuthorizationExpired('fixture expired during intent persistence')

        with patch.object(F, 'durable', side_effect=save), patch.object(T.subprocess, 'run') as process:
            with self.assertRaises(F.AuthorizationExpired):
                host.command(['FIXTURE-ROOT-HELPER'], authorize=check)
            process.assert_not_called()
        self.assertEqual(json.loads((host.directory / '0001-result.json').read_text())['status'],
                         'authorization_expired_before_dispatch')

    def test_expiry_between_tcp_proof_and_tcp_dispatch(self):
        host = T.HostIO(self.root / 'commands')
        pin = M.O.make_pin(M.FakeHost(M.Device()), M.RUN, 'nonce')
        returned = {'snapshot': M.snapshot(M.NEW)}
        expired = [False]

        def snapshot(row):
            expired[0] = True
            return M.snapshot(M.NEW)

        def check():
            if expired[0]:
                raise F.AuthorizationExpired('fixture expired after TCP proof')

        host.authorization_check = check
        with patch.object(host, 'inventory', return_value=[M.row(tid='3')]), \
                patch.object(host, 'stock_snapshot', side_effect=snapshot), \
                patch.object(T.subprocess, 'run') as process:
            with self.assertRaises(F.AuthorizationExpired):
                host.ensure_tcp(pin, returned)
            process.assert_not_called()

    def test_expiry_after_tcpip_prevents_new_connect_command(self):
        host = T.HostIO(self.root / 'commands')
        pin = M.O.make_pin(M.FakeHost(M.Device()), M.RUN, 'nonce')
        expired = [False]

        def check():
            if expired[0]:
                raise F.AuthorizationExpired('fixture expired after tcpip')

        def process(argv, **kwargs):
            expired[0] = True
            return subprocess.CompletedProcess(argv, 0, b'restarting in TCP mode port: 5555\n', b'')

        host.authorization_check = check
        with patch.object(host, 'inventory', return_value=[M.row(tid='3')]), \
                patch.object(host, 'stock_snapshot', return_value=M.snapshot(M.NEW)), \
                patch.object(T.subprocess, 'run', side_effect=process) as run:
            with self.assertRaises(F.AuthorizationExpired):
                host.ensure_tcp(pin, {'snapshot': M.snapshot(M.NEW)})
            self.assertEqual(run.call_count, 1)
            self.assertEqual(run.call_args.args[0], ['adb', '-t', '3', 'tcpip', '5555'])

    def test_missing_authorization_callback_cannot_dispatch_entry(self):
        host = T.HostIO(self.root / 'commands')
        with patch.object(host, 'command') as command:
            with self.assertRaises(F.Refused):
                host.entry({'initial_transport_id': '1'})
            command.assert_not_called()

    def test_verified_stock_readback_survives_later_expiry(self):
        expired = [False]
        real = M.Device.step

        def step(dev, label):
            if label == 'restore:healthy' and dev.counts.get(label, 0) == 2:
                expired[0] = True
            return real(dev, label)

        def check():
            if expired[0]:
                raise F.AuthorizationExpired('fixture expired after actual stock readback')

        with patch.object(M.Device, 'step', step):
            dev, host, result = self.trial(recheck=check)
        self.assertEqual(dev.writes, ['candidate', 'stock'])
        self.assertTrue(result['p10_restored'])
        self.assertFalse(result['cleanup_verified'])
        self.assertFalse(result['metadata_reverified'])
        self.assertEqual(result['outcome'], 'authorization_expired_no_new_command')

    def test_expiry_during_preentry_failure_preserves_modified_partition_fact(self):
        expired = [False]
        real = M.FakeObserver.start

        def start(observer):
            expired[0] = True
            return real(observer)

        def check():
            if expired[0]:
                raise F.AuthorizationExpired('fixture expired before preentry inverse')

        with patch.object(M.FakeObserver, 'start', start):
            dev, host, result = self.trial(behavior='not_ready', recheck=check)
        self.assertEqual(dev.writes, ['candidate'])
        self.assertEqual(host.entries, 0)
        self.assertTrue(result['partition_may_be_modified'])
        self.assertEqual(result['outcome'], 'authorization_expired_no_new_command')

    def test_inflight_completion_is_retained_then_new_command_refused(self):
        host = T.HostIO(self.root / 'commands')
        expired = [False]

        def check():
            if expired[0]:
                raise F.AuthorizationExpired('fixture expired after dispatch')

        def process(argv, **kwargs):
            expired[0] = True
            return subprocess.CompletedProcess(argv, 0, b'', b'')

        with patch.object(T.subprocess, 'run', side_effect=process) as run:
            self.assertEqual(host.command(['FIXTURE-INFLIGHT'], authorize=check).returncode, 0)
            with self.assertRaises(F.AuthorizationExpired):
                host.command(['FIXTURE-NEXT'], authorize=check)
            self.assertEqual(run.call_count, 1)

    def test_expiry_is_exclusive_and_admission_margin_is_checked(self):
        value = C.template()
        for key, item in value['parent_review'].items():
            if isinstance(item, bool):
                value['parent_review'][key] = True
        value['parent_review'].update(reviewer='OFFLINE ONLY', reviewed_at_utc='2026-11-06T20:00:00+00:00')
        path = self.root / 'review-FIXTURE.json'
        path.write_text(json.dumps(value))
        with self.assertRaises(F.AuthorizationExpired):
            C.review(path, F.sha(path.read_bytes()), dt.datetime(2026, 11, 6, 23, 3, tzinfo=dt.timezone.utc))
        with self.assertRaises(F.AuthorizationExpired):
            C.review(path, F.sha(path.read_bytes()), dt.datetime(2026, 11, 6, 22, 49, tzinfo=dt.timezone.utc), minimum_seconds=900)


if __name__ == '__main__':
    unittest.main()
