import ast
import dataclasses
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import threading
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
REPRODUCTIONS = []

def configure(module):
    global m, t
    m = module
    t = module.t
    for name in ('setUp', 'tearDown', 'mode', 'calls', 'events', 'observe'):
        setattr(IndependentCases, name, getattr(m.Cases, name))
    IndependentCases.setUpClass = classmethod(m.Cases.setUpClass.__func__)

class IndependentCases(unittest.TestCase):
    def save_repro(self, value):
        value['source_sha256'] = self.source_sha
        REPRODUCTIONS.append(value)
        (ROOT / 'evidence/reproductions.json').write_text(json.dumps(REPRODUCTIONS, indent=2) + '\n')

    def test_reproduce_expired_binding_at_request_dispatch(self):
        real_wall, real_mono = time.time, time.monotonic
        offset = 0.0
        probes = 0
        sends = []
        real_write = os.write
        self.binding = dataclasses.replace(self.binding, created_wall=real_wall()-179,
                                          created_monotonic=real_mono()-179)
        def probe(deadline):
            nonlocal probes, offset
            probes += 1
            if probes == 6:  # Last checked server query, after the final check_binding.
                offset = 1.5  # Within the real server probe's independent two-second cap.
        def write(fd, data):
            if bytes(data) == self.measure.REQUEST:
                sends.append(dict(wall_age=time.time()-self.binding.created_wall,
                                  monotonic_age=time.monotonic()-self.binding.created_monotonic))
            return real_write(fd, data)
        with patch.object(time, 'time', side_effect=lambda: real_wall()+offset), \
             patch.object(time, 'monotonic', side_effect=lambda: real_mono()+offset), \
             patch.object(t, 'server_version', side_effect=probe), \
             patch.object(os, 'write', side_effect=write):
            result = self.observe()
            self.assertEqual(probes, 6)
            self.assertEqual(len(sends), 1)
            self.assertGreater(sends[0]['wall_age'], 180)
            self.assertGreater(sends[0]['monotonic_age'], 180)
            self.assertEqual(result['result'], 'OBSERVED_MATCH')
            accepted = t.accept_completion(self.binding, exit_status=0, stdout=json.dumps(result).encode(),
                                           expected_source_sha256=self.source_sha)
            self.assertEqual(accepted, result)
            with self.assertRaises(t.Refused):
                t.check_binding(self.binding, self.deployment.host_clock_epoch())
        self.assertEqual((self.d/'request.bin').read_bytes(), self.measure.REQUEST)
        self.save_repro(dict(finding='freshness_expired_before_first_request_byte', probes=probes,
                             request_bytes=80, ages_at_send=sends[0], result=result['result'],
                             offline_acceptance='accepted', simulated_guard_delay_seconds=offset,
                             method='advance both clocks only at final server probe; actual guards/hash/install checks retained'))

    def test_readme_parent_recipe_attribute_is_absent(self):
        readme = (m.ROOT / 'README.md').read_text()
        blocks = readme.split('```python\n')
        self.assertEqual(len(blocks), 2)
        recipe = blocks[1].split('```')[0]
        tree = ast.parse(recipe)
        first_assert = next(n for n in tree.body if isinstance(n, ast.Assert))
        assertion = ast.unparse(first_assert)
        with self.assertRaises(AttributeError) as caught:
            exec(compile(ast.Module(body=[first_assert], type_ignores=[]), '<README assertion>', 'exec'),
                 dict(transport=t, TRANSPORT_SHA=self.source_sha))
        self.assertEqual(t.LOADED_SOURCE_SHA, self.source_sha)
        self.save_repro(dict(finding='readme_parent_recipe_missing_attribute', assertion=assertion,
                             error_type=type(caught.exception).__name__, working_attribute='LOADED_SOURCE_SHA'))

    def test_exact_popen_allowlist_and_environment(self):
        self.popen.reset_mock()
        with patch.dict(os.environ, {'ADB_SERVER_SOCKET':'tcp:invalid:1', 'ANDROID_ADB_SERVER_PORT':'9999',
                                    'ADB_VENDOR_KEYS':'DO_NOT_OPEN', 'LD_PRELOAD':'DO_NOT_LOAD'}):
            result = self.observe()
        calls = self.calls()
        base = ['-H','127.0.0.1','-P','5037']
        self.assertEqual(calls, [base+['devices','-l'],base+['-t','17','features'],base+['devices','-l'],
                                  base+['-t','17','shell','-T','-e','none','rescue-v1'],base+['devices','-l']])
        for call in self.popen.call_args_list:
            self.assertEqual(set(call.kwargs['env']), {'HOME','PATH'})
            self.assertEqual(call.kwargs['env']['PATH'], '/usr/bin:/bin')
            self.assertIs(call.kwargs['close_fds'], True)
            self.assertEqual(call.kwargs['bufsize'], 0)
        self.assertEqual(result['wire_opcode'], 2)

    def test_expiration_observed_at_last_check_blocks_request(self):
        original = t.check_binding
        count = 0
        def check(binding, epoch):
            nonlocal count
            count += 1
            if count == 7:
                binding = dataclasses.replace(binding, created_wall=time.time()-181)
            return original(binding, epoch)
        with patch.object(t, 'check_binding', side_effect=check), self.assertRaises(t.Refused):
            self.observe()
        self.assertEqual(count, 7)
        self.assertFalse((self.d/'request.bin').exists())

    def test_duplicate_ambiguous_and_malformed_usb_rows_reject(self):
        good = b'DEVICE_SERIAL_REDACTED device usb:1-3.2 product:p00a_target_rescue model:P00A_target_rescue device:p00a transport_id:17'
        header = b'List of devices attached\n'
        cases = [good+b'\n'+good, good+b' transport_id:18', good.replace(b'transport_id:17',b'transport_id:017'),
                 good+b'\nother device usb:2-1 transport_id:18', good.replace(b'device usb:',b'unauthorized usb:'),
                 good.replace(b'usb:1-3.2',b'usb:1-3.3'),good.replace(b'product:p00a_target_rescue',b'product:stock')]
        for raw in cases:
            with self.subTest(raw=raw), self.assertRaises(t.Refused):
                t.select_usb(header+raw+b'\n', self.binding)
        self.assertEqual(t.select_usb(header+good+b'\n', self.binding)['transport_id'], '17')

    def local_child(self, mode, seconds=.25):
        with patch.object(subprocess, 'Popen', self.popen):
            child = t.PipeStream([sys.executable,'-B',str(ROOT/'scripts/extra_child.py'),mode], time.monotonic()+seconds)
        self.children.append(child.proc)
        return child

    def test_stderr_eof_before_reply_succeeds(self):
        child = self.local_child('stderr_eof_then_valid', 1)
        try:
            result = self.measure.measure(child, 1)
            child.finish()
            self.assertEqual(result['result'], 'OBSERVED_MATCH')
        finally:
            child.dispose()

    def test_pipe_eof_without_process_exit_is_bounded(self):
        child = self.local_child('close_both_then_hang')
        started = time.monotonic()
        try:
            with self.assertRaises(subprocess.TimeoutExpired):
                child.finish()
        finally:
            child.dispose()
        self.assertLess(time.monotonic()-started, 1.6)

    def test_unbounded_stderr_still_honors_deadline(self):
        child = self.local_child('stderr_flood_without_exit')
        started = time.monotonic()
        try:
            with self.assertRaises(TimeoutError):
                self.measure.measure(child, .25)
            self.assertEqual(child.stderr_retained, b'')
        finally:
            child.dispose()
        self.assertLess(time.monotonic()-started, 1.6)

    def test_broken_stdin_sends_no_success(self):
        child = self.local_child('broken_stdin')
        try:
            time.sleep(.08)
            with self.assertRaises(BrokenPipeError):
                self.measure.measure(child, .25)
        finally:
            child.dispose()

    def test_premature_stdout_refuses(self):
        child = self.local_child('early_stdout')
        try:
            time.sleep(.08)
            with self.assertRaises(t.Refused):
                self.measure.measure(child, .25)
        finally:
            child.dispose()

    def test_discovery_stdout_flood_bounded(self):
        child = self.local_child('discovery_flood')
        try:
            with self.assertRaises(t.Refused):
                child.finish(t.OUTPUT_LIMIT)
        finally:
            child.dispose()

    def test_terminal_fsync_failure_with_visible_match_not_accepted(self):
        fsync = os.fsync
        hits = 0
        def fail_terminal(fd):
            nonlocal hits
            # Fail fsync for the terminal match, without claiming it was durable.
            path = self.d/'runs'/self.binding.rescue_session_id/'events.jsonl'
            if path.exists() and b'OBSERVED_MATCH' in path.read_bytes():
                hits += 1
                raise OSError('owned fsync failure')
            return fsync(fd)
        with patch.object(os, 'fsync', side_effect=fail_terminal), self.assertRaises(OSError):
            self.observe()
        self.assertGreaterEqual(hits, 2)
        rows = self.events()
        match = next(r for r in rows if r['result'] == 'OBSERVED_MATCH')
        for status in (None, 1, 0):
            with self.assertRaises(t.Refused):
                t.accept_completion(self.binding, exit_status=status, stdout=json.dumps(match).encode(),
                                    expected_source_sha256=self.source_sha)
        count = len(self.calls())
        with self.assertRaises(FileExistsError):
            self.observe()
        self.assertEqual(count, len(self.calls()))

    def test_completion_duplicate_nonfinite_and_wrong_provenance_refuse(self):
        result = self.observe()
        out = json.dumps(result).encode()
        for raw in (out[:-1]+b',"result":"OBSERVED_MATCH"}', out.replace(str(result['elapsed_seconds']).encode(), b'NaN')):
            with self.assertRaises(t.Refused):
                t.accept_completion(self.binding, exit_status=0, stdout=raw, expected_source_sha256=self.source_sha)
        path = Path(result['terminal_evidence'])
        rows = self.events()
        rows[0]['source_sha256'] = '0'*64
        path.write_text(''.join(json.dumps(r)+'\n' for r in rows))
        with self.assertRaises(t.Refused):
            t.accept_completion(self.binding, exit_status=0, stdout=out, expected_source_sha256=self.source_sha)

    def test_server_version_requires_eof_and_shared_deadline(self):
        # Synchronous socketpair response, with peer kept open: no TCP or worker.
        original = t.server_version
        self.patches[4].stop()
        try:
            host, peer = socket.socketpair()
            peer.sendall(b'OKAY00040029')
            started = time.monotonic()
            try:
                with patch.object(socket, 'create_connection', return_value=host), self.assertRaises(TimeoutError):
                    t.server_version(time.monotonic()+.12)
                self.assertEqual(peer.recv(16), b'000chost:version')
                self.assertLess(time.monotonic()-started, .7)
            finally:
                peer.close()
        finally:
            self.patches[4].start()

    def test_plan_and_offline_acceptance_have_no_child_or_socket_operations(self):
        with patch.object(subprocess, 'Popen', side_effect=AssertionError('child forbidden')), \
             patch.object(socket, 'create_connection', side_effect=AssertionError('connect forbidden')):
            with patch.object(sys, 'argv', ['transport.py']):
                t.main()
            # Invalid live completion must refuse using local inputs only.
            with self.assertRaises(t.Refused):
                t.accept_completion(self.binding, exit_status=None, stdout=b'', expected_source_sha256=self.source_sha)
