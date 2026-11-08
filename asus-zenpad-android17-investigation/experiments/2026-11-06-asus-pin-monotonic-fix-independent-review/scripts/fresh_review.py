#!/usr/bin/env python3
"""Fresh independent tests of unchanged copied production code; offline boundaries only."""
import contextlib
import copy
import io
import json
import os
from pathlib import Path
import sys
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
SNAP = ROOT / 'snapshot/2026-11-06-asus-rescue-pin-monotonic-fix'
BLOCKED = []
def audit(event, args):
    if event in {'subprocess.Popen', 'os.system', 'os.posix_spawn', 'os.fork',
                 'os.forkpty', 'os.exec', 'pty.spawn'} or event.startswith('socket.'):
        BLOCKED.append(event)
        raise AssertionError('OFFLINE boundary blocked: ' + event)
sys.addaudithook(audit)
sys.dont_write_bytecode = True
sys.path[:0] = [str(SNAP / 'source'), str(SNAP / 'tests')]
import subprocess
from unittest.mock import patch
import test_adapter as supplied
import adapter as a
b = a.b
OUT = ROOT / 'evidence' / ('fresh-' + str(time.time_ns()))
OUT.mkdir()
EPOCH_A = 'darwin:11111111-1111-4111-8111-111111111111'
EPOCH_B = 'darwin:22222222-2222-4222-8222-222222222222'

class Review(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stock, cls.full, cls.local = a.verify_local()
        cls.code = a.code_receipt()['sha256']

    def setUp(self):
        self.directory = OUT / self._testMethodName
        self.directory.mkdir()
        self.contract_directory = SNAP / 'evidence' / OUT.name / self._testMethodName
        self.contract_directory.mkdir(parents=True)
        self.clock = {'wall': 2000000000.0, 'mono': 1000.0}
        self.epoch = EPOCH_A
        self.fake = supplied.Fake(self.stock)
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(patch.object(time, 'time', side_effect=lambda: self.clock['wall']))
        self.stack.enter_context(patch.object(time, 'monotonic', side_effect=lambda: self.clock['mono']))
        self.stack.enter_context(patch.object(a, 'host_clock_epoch', side_effect=lambda: self.epoch))
        self.stack.enter_context(patch.object(a, 'RUNS', self.directory / 'runs'))
        self.stack.enter_context(patch.object(subprocess, 'run', side_effect=self.fake))
        lock = self.directory / 'fixture.lock'
        lock.touch()
        self.stack.enter_context(patch.object(b, 'EXECUTE_LOCK', lock))

    def note(self, **fields):
        (self.directory / 'observations.json').write_text(json.dumps(fields, indent=2) + '\n')

    def contract(self, phase):
        c = supplied.contract(phase)
        c['valid_until'] = self.clock['wall'] + 590
        return c

    def transport(self, pin=True):
        p = supplied.pin() if pin else None
        g = a.Guard(self.contract('install'), supplied.RUN, 'install', self.code, p)
        j = a.Journal(self.directory, 'install', supplied.RUN, self.code)
        j.state['pin'] = p
        j.save()
        return a.Transport(self.directory, j, 'install', g)

    def stage(self, t):
        t.setup()
        t.stage('stock', self.stock)
        t.stage('candidate', self.full)
        t.read()

    def terminal(self, t, count):
        self.assertTrue(t.guard.stopped)
        for operation in (t.cleanup, lambda: t.write('stock'), t.usb_enumeration):
            with self.assertRaises(b.UncertainTransport):
                operation()
            self.assertEqual(len(self.fake.calls), count)

    def capture(self):
        directory = a.reserve(supplied.RUN, 'pin-install')
        g = a.Guard(self.contract('pin-install'), supplied.RUN, 'pin-install', self.code)
        j = a.Journal(directory, 'pin-install', supplied.RUN, self.code)
        t = a.Transport(directory, j, 'pin-install', g)
        p = t.usb_snapshot()
        a.durable(directory / 'pin.json', p)
        j.finish('healthy_stock_usb_pin_captured', pin=p, pin_sha256=a.object_sha(p))
        return directory, j, p

    def invoke(self, phase, success=True):
        path = self.contract_directory / (phase + '-contract.json')
        c = self.contract(phase)
        if phase in ('pin-restore', 'restore'):
            c['install_completion_token'] = self.token
        a.durable(path, c)
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            result = a.main([phase, '--execute', '--run-id', supplied.RUN,
                             '--contract', str(path), '--supervised', '--physical-fallback-present'])
        (self.directory / (phase + '-stdout.json')).write_text(stdout.getvalue())
        (self.directory / (phase + '-stderr.txt')).write_text(stderr.getvalue())
        self.assertEqual(result, 0 if success else 2, (stdout.getvalue(), stderr.getvalue()))
        if success and phase == 'install':
            self.token = json.loads(stdout.getvalue())['install_completion_token']
        return a.json_file(a.RUNS / supplied.RUN / phase / 'state.json') if success else None

    def test_nested_write_refused_at_200_elapsed_despite_100_wall(self):
        t = self.transport()
        self.stage(t)
        self.clock.update(wall=2000000100.0, mono=1200.0)
        count = len(self.fake.calls)
        with self.assertRaises(b.UncertainTransport):
            t.write('candidate')
        self.assertEqual(self.fake.inner.writes, [])
        self.terminal(t, count)
        self.note(wall_age=100, monotonic_age=200, actual_nested_writes=self.fake.inner.writes,
                  stopped=t.guard.stopped, commands_before=count, commands_after=len(self.fake.calls))

    def test_serialized_pin_refused_after_400_elapsed(self):
        directory, j, p = self.capture()
        self.clock.update(wall=2000000100.0, mono=1400.0)
        count = len(self.fake.calls)
        with self.assertRaises(b.Refused):
            a.load_pin(supplied.RUN, 'install', self.code)
        self.assertEqual(len(self.fake.calls), count)
        self.note(wall_age=100, monotonic_age=400, accepted=False, pin=p,
                  commands_before=count, commands_after=len(self.fake.calls))

    def test_actual_nested_write_final_evidence_consumes_pin_deadline(self):
        t = self.transport()
        self.stage(t)
        original = a.durable
        trip = []
        def persist(path, value):
            original(path, value)
            if 'dd if=' + t.vault + '/candidate.bin of=' + b.BLOCK in (value.get('stdin') or ''):
                trip.append(len(self.fake.calls))
                self.clock.update(wall=2000000100.0, mono=1180.0)
        with patch.object(a, 'durable', side_effect=persist), self.assertRaises(b.UncertainTransport):
            t.write('candidate')
        self.assertEqual(len(trip), 1)
        self.assertEqual(self.fake.inner.writes, [])
        self.assertEqual(t.journal.state['partition_status'], 'exact_stock')
        self.assertFalse(t.journal.state['partition_may_be_modified'])
        self.assertEqual(t.journal.state['write_dispatches'][0]['delivery'], 'not_dispatched_run_consumed')
        self.terminal(t, trip[0])
        self.note(pin_deadline=1180, dispatches=t.journal.state['write_dispatches'],
                  actual_nested_writes=self.fake.inner.writes, stopped=t.guard.stopped)

    def test_source_checks_consume_remaining_pin_time_at_final_dispatch(self):
        t = self.transport()
        original_durable, original_sources = a.durable, a.check_sources
        armed = []
        def persist(path, value):
            original_durable(path, value)
            if value.get('argv') == ['adb', 'devices', '-l']:
                armed.append(True)
        def slow_sources():
            original_sources()
            if armed:
                self.clock.update(wall=2000000100.0, mono=1180.0)
        with patch.object(a, 'durable', side_effect=persist), patch.object(a, 'check_sources', side_effect=slow_sources):
            with self.assertRaises(b.UncertainTransport):
                t.usb_enumeration()
        self.assertTrue(armed)
        self.terminal(t, 0)
        self.note(expired_after_source_check=True, commands=0, stopped=t.guard.stopped)

    def test_late_pin_assignment_caps_guard_and_final_check_catches_elapsed(self):
        p = supplied.pin()
        self.clock.update(wall=2000000100.0, mono=1179.0)
        t = self.transport(pin=False)
        self.assertEqual(t.guard.end_mono, 1769)
        t.guard.pin = p
        t.guard.check()
        self.assertEqual(t.guard.end_mono, 1180)
        original = a.validate_pin
        def elapsed(*args, **kwargs):
            original(*args, **kwargs)
            self.clock['mono'] = 1180.0
        with patch.object(a, 'validate_pin', side_effect=elapsed), self.assertRaises(b.UncertainTransport):
            t.usb_enumeration()
        self.terminal(t, 0)
        self.note(late_pin_deadline=t.guard.end_mono, final_monotonic=self.clock['mono'], commands=0)

    def test_contract_shorter_than_pin_still_wins(self):
        t = self.transport()
        t.guard.end_mono = 1010
        self.clock.update(wall=2000000005.0, mono=1010.0)
        with self.assertRaises(b.UncertainTransport):
            t.usb_enumeration()
        self.terminal(t, 0)

    def test_main_late_pin_assignment_rechecks_expiry_after_load(self):
        self.invoke('pin-install')
        original = a.load_pin
        loaded = []
        def elapsed(*args, **kwargs):
            pin = original(*args, **kwargs)
            loaded.append(pin)
            self.clock.update(wall=2000000100.0, mono=1180.0)
            return pin
        count = len(self.fake.calls)
        with patch.object(a, 'load_pin', side_effect=elapsed):
            self.invoke('install', success=False)
        self.assertEqual(len(loaded), 1)
        self.assertEqual(len(self.fake.calls), count)
        self.assertFalse((a.RUNS / supplied.RUN / 'install').exists())
        self.note(pin_was_loaded=True, expired_before_main_assignment=True,
                  install_reserved=False, commands_after_capture=0)

    def test_host_epoch_change_at_actual_nested_write_evidence_boundary(self):
        t = self.transport()
        self.stage(t)
        original = a.durable
        trip = []
        def persist(path, value):
            original(path, value)
            if 'dd if=' + t.vault + '/candidate.bin of=' + b.BLOCK in (value.get('stdin') or ''):
                trip.append(len(self.fake.calls))
                self.epoch = EPOCH_B
        with patch.object(a, 'durable', side_effect=persist), self.assertRaises(b.UncertainTransport):
            t.write('candidate')
        self.assertEqual(len(trip), 1)
        self.assertEqual(self.fake.inner.writes, [])
        self.terminal(t, trip[0])
        self.note(old_epoch=EPOCH_A, current_epoch=EPOCH_B,
                  dispatches=t.journal.state['write_dispatches'], writes=self.fake.inner.writes)

    def test_capture_age_starts_before_usb_observation(self):
        def consume(argv, script):
            self.clock['wall'] += 15
            self.clock['mono'] += 15
        self.fake.before = consume
        directory, j, p = self.capture()
        self.assertEqual(p['created_at'], 2000000000.0)
        self.assertEqual(p['created_monotonic'], 1000.0)
        age = self.clock['mono'] - p['created_monotonic']
        self.assertGreater(age, 180)
        with self.assertRaises(b.Refused):
            a.load_pin(supplied.RUN, 'install', self.code)
        self.note(capture_age=age, pin=p, serialized_pin_accepted=False)

    def test_health_observation_cannot_refresh_active_pin(self):
        t = self.transport()
        p = copy.deepcopy(t.guard.pin)
        self.clock.update(wall=2000000100.0, mono=1170.0)
        t.healthy()
        self.assertEqual(t.guard.pin, p)
        self.assertEqual(t.guard.end_mono, 1180)
        self.clock['mono'] = 1180.0
        count = len(self.fake.calls)
        with self.assertRaises(b.UncertainTransport):
            t.write('candidate')
        self.terminal(t, count)

    def test_host_epoch_change_at_live_boundary_stops_every_later_command(self):
        t = self.transport()
        self.epoch = EPOCH_B
        with self.assertRaises(b.UncertainTransport):
            t.write('candidate')
        self.terminal(t, 0)

    def test_serialized_schema_epoch_and_future_monotonic_rejected(self):
        directory, j, p = self.capture()
        variants = [{'schema': 1}, {'created_monotonic': None},
                    {'created_monotonic': 1001.0}, {'created_monotonic': -1},
                    {'host_clock_epoch': EPOCH_B}, {'host_clock_epoch': None},
                    {'created_at': 2000000001.0}]
        count = len(self.fake.calls)
        for change in variants:
            with self.subTest(change=change):
                edited = {**p, **change}
                a.durable(directory / 'pin.json', edited)
                j.finish('healthy_stock_usb_pin_captured', pin=edited, pin_sha256=a.object_sha(edited))
                with self.assertRaises(b.Refused):
                    a.load_pin(supplied.RUN, 'install', self.code)
                self.assertEqual(len(self.fake.calls), count)
        self.note(refused_variants=variants, commands_after_capture=0)

    def test_wall_expiry_still_refuses_with_fresh_monotonic(self):
        t = self.transport()
        self.clock.update(wall=2000000181.0, mono=1001.0)
        with self.assertRaises(b.UncertainTransport):
            t.write('candidate')
        self.terminal(t, 0)

    def test_historical_install_survives_epoch_change_with_fresh_restore_pin(self):
        self.invoke('pin-install')
        self.clock.update(wall=2000000001.0, mono=1001.0)
        installed = self.invoke('install')
        old = installed['pin']
        self.clock.update(wall=2000000401.0, mono=50.0)
        self.epoch = EPOCH_B
        count = len(self.fake.calls)
        # Historical validation must not query the current epoch or age.
        with patch.object(a, 'host_clock_epoch', side_effect=AssertionError('historical epoch query')):
            linked, _ = a.check_install(supplied.RUN, self.code, self.token)
        self.assertEqual(linked['pin'], old)
        self.assertEqual(count, len(self.fake.calls))
        with self.assertRaises(b.Refused):
            a.validate_pin(old, supplied.RUN, self.code)
        self.fake.row['transport_id'] = '23'
        fresh = self.invoke('pin-restore')['pin']
        self.assertEqual(fresh['host_clock_epoch'], EPOCH_B)
        self.clock.update(wall=2000000402.0, mono=51.0)
        state = self.invoke('restore')
        self.assertEqual(state['outcome'], 'restored_full_hash_verified')
        self.assertEqual([x['source'] for x in self.fake.inner.writes], ['candidate', 'stock'])
        self.note(old_pin=old, new_pin=fresh, restore_outcome=state['outcome'],
                  writes=self.fake.inner.writes, fixture_only=True)

    def test_historical_link_does_not_allow_expired_current_restore_pin(self):
        self.invoke('pin-install')
        self.clock.update(wall=2000000001.0, mono=1001.0)
        self.invoke('install')
        self.clock.update(wall=2000000401.0, mono=1401.0)
        self.invoke('pin-restore')
        self.clock.update(wall=2000000501.0, mono=1801.0)
        count = len(self.fake.calls)
        a.check_install(supplied.RUN, self.code, self.token)
        self.invoke('restore', success=False)
        self.assertEqual(len(self.fake.calls), count)
        self.assertEqual([x['source'] for x in self.fake.inner.writes], ['candidate'])
        self.note(current_restore_pin_wall_age=100, current_restore_pin_monotonic_age=400,
                  no_restore_commands=True, writes=self.fake.inner.writes)

    def test_historical_binding_still_rejects_source_or_capture_tampering(self):
        self.invoke('pin-install')
        self.clock['wall'] += 1
        self.invoke('install')
        path = a.RUNS / supplied.RUN / 'install/state.json'
        original = a.json_file(path)
        for change in ({'schema': 1}, {'code_sha256': '0' * 64}, {'properties': {}},
                       {'host_clock_epoch': None}, {'candidate_sha256': '0' * 64}):
            state = copy.deepcopy(original)
            state['pin'].update(change)
            a.durable(path, state)
            with self.subTest(change=change), self.assertRaises(b.Refused):
                a.check_install(supplied.RUN, self.code, self.token)
        a.durable(path, original)
        capture = path.parent / original['captures'][-1]['file']
        capture.write_bytes(self.stock)
        with self.assertRaises(b.Refused):
            a.check_install(supplied.RUN, self.code, self.token)

class HostEpoch(unittest.TestCase):
    def test_actual_host_epoch_stable_readonly(self):
        first, second = a.host_clock_epoch(), a.host_clock_epoch()
        self.assertEqual(first, second)
        self.assertRegex(first, r'^(linux|darwin):[0-9a-f-]{36}$')
        (OUT / 'actual-host-epoch.json').write_text(json.dumps({'first': first, 'second': second}) + '\n')

    def test_linux_epoch_reads_only_host_boot_id(self):
        requested = []
        def read(path, *args, **kwargs):
            requested.append(str(path))
            return EPOCH_A.split(':')[1] + '\n'
        with patch.object(sys, 'platform', 'linux'), patch.object(Path, 'read_text', read):
            self.assertEqual(a.host_clock_epoch(), 'linux:' + EPOCH_A.split(':')[1])
        self.assertEqual(requested, ['/proc/sys/kernel/random/boot_id'])

    def test_linux_invalid_or_missing_epoch_refuses(self):
        with patch.object(sys, 'platform', 'linux'):
            for value in ('', 'not-a-uuid', EPOCH_A.split(':')[1].upper()):
                # The selected UUID is all numeric; use a lettered uppercase UUID explicitly.
                if value == EPOCH_A.split(':')[1].upper():
                    value = 'ABCDEFAB-1111-4111-8111-111111111111'
                with self.subTest(value=value), patch.object(Path, 'read_text', return_value=value):
                    with self.assertRaises((b.Refused, ValueError)):
                        a.host_clock_epoch()
            with patch.object(Path, 'read_text', side_effect=OSError('fixture unavailable')):
                with self.assertRaises(OSError):
                    a.host_clock_epoch()

    def test_unsupported_host_refuses(self):
        with patch.object(sys, 'platform', 'unsupported'), self.assertRaises(b.Refused):
            a.host_clock_epoch()

    def test_darwin_sysctl_success_and_failures(self):
        import ctypes
        value = b'ABCDEFAB-1111-4111-8111-111111111111\0'
        class Query:
            def __init__(self, failure=None):
                self.failure, self.calls = failure, []
            def __call__(self, name, buffer, size, new, new_size):
                self.calls.append(name.decode())
                if self.failure == 'first' or (self.failure == 'second' and buffer is not None):
                    return -1
                size._obj.value = 0 if self.failure == 'empty' else 129 if self.failure == 'oversize' else len(value)
                if buffer is not None:
                    buffer.value = value[:-1] if self.failure != 'malformed' else b'invalid'
                return 0
        with patch.object(sys, 'platform', 'darwin'):
            query = Query()
            with patch.object(ctypes, 'CDLL', return_value=type('Lib', (), {'sysctlbyname': query})()):
                self.assertEqual(a.host_clock_epoch(), 'darwin:abcdefab-1111-4111-8111-111111111111')
            self.assertEqual(query.calls, ['kern.bootsessionuuid', 'kern.bootsessionuuid'])
            for failure in ('first', 'second', 'empty', 'oversize', 'malformed'):
                query = Query(failure)
                with self.subTest(failure=failure), patch.object(ctypes, 'CDLL', return_value=type('Lib', (), {'sysctlbyname': query})()):
                    with self.assertRaises((b.Refused, ValueError)):
                        a.host_clock_epoch()

def main():
    stream = io.StringIO()
    suite = unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(Review),
                               unittest.defaultTestLoader.loadTestsFromTestCase(HostEpoch)])
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    (OUT / 'tests.txt').write_text(stream.getvalue())
    receipt = dict(tests=result.testsRun, failures=len(result.failures), errors=len(result.errors),
                   failure_details=[dict(test=str(t), traceback=s) for t, s in result.failures],
                   error_details=[dict(test=str(t), traceback=s) for t, s in result.errors],
                   audit_blocked_events=BLOCKED, code=a.code_receipt(),
                   test_sha256=a.sha(Path(__file__).read_bytes()),
                   actual_subprocess_calls=0, network_operations=0, device_contacted=False,
                   scope='Offline typed fixtures; no physical, timing, or transport success claimed')
    (OUT / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    (OUT / 'fresh_review.py').write_bytes(Path(__file__).read_bytes())
    print(stream.getvalue())
    print(json.dumps({'evidence': str(OUT), **{k: receipt[k] for k in ('tests', 'failures', 'errors', 'audit_blocked_events')}}))
    return 0 if result.wasSuccessful() and not BLOCKED else 1

if __name__ == '__main__':
    raise SystemExit(main())
