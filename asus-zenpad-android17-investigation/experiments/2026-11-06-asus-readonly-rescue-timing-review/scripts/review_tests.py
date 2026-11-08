"""Local-only independent tests of byte-identical reviewed Python snapshot."""
from pathlib import Path
import contextlib
import hashlib
import importlib.util
import io
import json
import math
import os
import socket
import struct
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parents[1]
WORKSPACE = HERE.parent
sys.path.insert(0, str(HERE / 'snapshot/source'))
import measure
measure.BUILD = WORKSPACE / '2026-11-06-asus-stock-only-ram-rescue-build'
import test_measure

REPLY = struct.pack('<4sII', b'RSC1', 0x82, 48) + b'REVIEW_SECRET_TOKEN'.ljust(32, b'_') + b'\x01' * 16
assert len(REPLY) == 60

def read_request(peer):
    data = bytearray()
    while len(data) < 80:
        part = peer.recv(80 - len(data))
        if not part:
            break
        data.extend(part)
    return bytes(data)

class IndependentTests(unittest.TestCase):
    def test_actual_deadline_across_slow_fragments(self):
        host, peer = socket.socketpair()
        result = {}
        def server():
            with peer:
                result['request'] = read_request(peer)
                try:
                    for b in REPLY:
                        peer.sendall(bytes([b]))
                        time.sleep(.025)
                except (BrokenPipeError, ConnectionResetError):
                    result['closed'] = True
        t = threading.Thread(target=server)
        t.start()
        start = time.monotonic()
        with self.assertRaises(TimeoutError):
            measure.measure(host, .12)
        elapsed = time.monotonic() - start
        t.join(2)
        self.assertFalse(t.is_alive())
        self.assertTrue(result['closed'])
        self.assertEqual(result['request'], measure.REQUEST)
        self.assertLess(elapsed, .5)
        self.assertEqual(host.fileno(), -1)

    def test_actual_send_backpressure_is_bounded(self):
        host, peer = socket.socketpair()
        try:
            host.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1024)
            host.setblocking(False)
            while True:
                try:
                    host.send(b'z' * 4096)
                except BlockingIOError:
                    break
            start = time.monotonic()
            with self.assertRaises(TimeoutError):
                measure.measure(host, .08)
            self.assertLess(time.monotonic() - start, .5)
            self.assertEqual(host.fileno(), -1)
        finally:
            host.close(); peer.close()

    def test_each_bitmap_position_and_nonbinary_byte(self):
        for index in range(16):
            for byte in (0, 2, 255):
                body = bytearray(REPLY)
                body[44 + index] = byte
                stream = test_measure.FakeStream(bytes(body))
                with self.assertRaises(ValueError):
                    measure.measure(stream, 1)
                self.assertTrue(stream.closed)
                self.assertEqual(stream.requests, [measure.REQUEST])

    def test_all_reply_truncation_points(self):
        for length in range(60):
            stream = test_measure.FakeStream(REPLY[:length])
            with self.assertRaises(EOFError):
                measure.measure(stream, 1)
            self.assertTrue(stream.closed)
            self.assertEqual(stream.requests, [measure.REQUEST])

    def test_socket_errors_close_without_second_request(self):
        for method in ('settimeout', 'sendall', 'recv'):
            stream = test_measure.FakeStream(REPLY)
            with patch.object(stream, method, side_effect=OSError('injected local failure')):
                with self.assertRaises(OSError):
                    measure.measure(stream, 1)
            self.assertTrue(stream.closed)
            self.assertLessEqual(len(stream.requests), 1)

    def cli(self, fd=None, evidence=None, extra=()):
        args = [] if fd is None else ['--execute', '--fd', str(fd), '--evidence', str(evidence), '--seconds', '1']
        wrapper = 'import sys; from pathlib import Path; import measure; measure.BUILD=Path(sys.argv.pop(1)); measure.main()'
        return subprocess.Popen([sys.executable, '-B', '-c', wrapper, str(measure.BUILD), *args, *extra],
            cwd=HERE / 'snapshot/source', pass_fds=() if fd is None else (fd,),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    def test_plan_only_creates_nothing(self):
        p = self.cli()
        out, err = p.communicate(timeout=5)
        self.assertEqual(p.returncode, 0, err)
        self.assertEqual(json.loads(out)['mode'], 'PLAN_ONLY')
        self.assertFalse(json.loads(out)['opens_transport'])

    def test_actual_cli_durable_success_and_eof_without_token(self):
        with tempfile.TemporaryDirectory(dir=HERE / 'evidence') as directory:
            host, peer = socket.socketpair()
            peer.settimeout(3)
            evidence = Path(directory) / 'run.jsonl'
            p = self.cli(host.fileno(), evidence)
            host.close()
            with peer:
                self.assertEqual(read_request(peer), measure.REQUEST)
                initial = [json.loads(x) for x in evidence.read_text().splitlines()]
                self.assertEqual(initial[0]['result'], 'UNKNOWN')
                for i in range(0, len(REPLY), 2):
                    peer.sendall(REPLY[i:i+2])
                self.assertEqual(peer.recv(1), b'')
            out, err = p.communicate(timeout=5)
            self.assertEqual(p.returncode, 0, err)
            data = evidence.read_text()
            rows = [json.loads(x) for x in data.splitlines()]
            self.assertEqual([r['result'] for r in rows], ['UNKNOWN', 'OBSERVED_MATCH'])
            self.assertEqual(json.loads(out), rows[1])
            self.assertEqual(evidence.stat().st_mode & 0o777, 0o600)
            self.assertNotIn(REPLY[12:44].decode(), data + out + err)

    def test_actual_cli_rejection_and_evidence_exclusive(self):
        with tempfile.TemporaryDirectory(dir=HERE / 'evidence') as directory:
            evidence = Path(directory) / 'run.jsonl'
            host, peer = socket.socketpair()
            peer.settimeout(3)
            p = self.cli(host.fileno(), evidence)
            host.close()
            with peer:
                self.assertEqual(read_request(peer), measure.REQUEST)
                peer.sendall(struct.pack('<4sII', b'RSC1', 0xff, 100))
                self.assertEqual(peer.recv(1), b'')
            out, err = p.communicate(timeout=5)
            self.assertNotEqual(p.returncode, 0)
            rows = [json.loads(x) for x in evidence.read_text().splitlines()]
            self.assertEqual([r['result'] for r in rows], ['UNKNOWN', 'UNKNOWN'])
            self.assertNotIn('OBSERVED_MATCH', out)
            before = evidence.read_bytes()
            host, peer = socket.socketpair()
            peer.settimeout(3)
            p = self.cli(host.fileno(), evidence)
            host.close()
            self.assertEqual(peer.recv(1), b'')
            out, err = p.communicate(timeout=5)
            peer.close()
            self.assertNotEqual(p.returncode, 0)
            self.assertEqual(evidence.read_bytes(), before)

    def test_durability_order_and_failed_final_fsync(self):
        with tempfile.TemporaryDirectory(dir=HERE / 'evidence') as directory:
            evidence = Path(directory) / 'run.jsonl'
            host, peer = socket.socketpair()
            peer.sendall(REPLY)
            syncs = []
            real_fsync = os.fsync
            def fsync(fd):
                syncs.append(fd)
                if len(syncs) == 3:
                    raise OSError('injected final fsync failure')
                return real_fsync(fd)
            argv = ['measure.py','--execute','--fd',str(host.fileno()),'--evidence',str(evidence)]
            with patch.object(sys, 'argv', argv), patch.object(measure.os, 'fsync', side_effect=fsync):
                with self.assertRaisesRegex(OSError, 'final fsync failure'):
                    measure.main()
            self.assertEqual(read_request(peer), measure.REQUEST)
            self.assertEqual(peer.recv(1), b'')
            peer.close()
            rows = [json.loads(x) for x in evidence.read_text().splitlines()]
            self.assertEqual([r['result'] for r in rows], ['UNKNOWN','OBSERVED_MATCH','UNKNOWN'])
            self.assertEqual(rows[-1]['error_type'], 'OSError')
            self.assertEqual(len(syncs), 4)

    def test_initial_evidence_sync_failure_sends_nothing(self):
        with tempfile.TemporaryDirectory(dir=HERE / 'evidence') as directory:
            evidence = Path(directory) / 'run.jsonl'
            host, peer = socket.socketpair()
            try:
                argv = ['measure.py','--execute','--fd',str(host.fileno()),'--evidence',str(evidence)]
                with patch.object(sys, 'argv', argv), patch.object(measure.os, 'fsync', side_effect=OSError('initial sync failed')):
                    with self.assertRaisesRegex(OSError, 'initial sync failed'):
                        measure.main()
                peer.settimeout(.03)
                with self.assertRaises(TimeoutError):
                    peer.recv(1)
                self.assertEqual(json.loads(evidence.read_text())['result'], 'UNKNOWN')
            finally:
                host.close(); peer.close()

    def test_wrong_or_unconnected_unix_socket_is_closed_without_request(self):
        with tempfile.TemporaryDirectory(dir=HERE / 'evidence') as directory:
            host, peer = socket.socketpair(type=socket.SOCK_DGRAM)
            peer.settimeout(3)
            p = self.cli(host.fileno(), Path(directory) / 'dgram.jsonl')
            host.close()
            out, err = p.communicate(timeout=5)
            self.assertNotEqual(p.returncode, 0)
            peer.settimeout(.03)
            with self.assertRaises((TimeoutError, ConnectionResetError)):
                peer.recv(100)
            peer.close()
            rows = [json.loads(x) for x in (Path(directory) / 'dgram.jsonl').read_text().splitlines()]
            self.assertEqual([r['result'] for r in rows], ['UNKNOWN', 'UNKNOWN'])
            host = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            p = self.cli(host.fileno(), Path(directory) / 'unconnected.jsonl')
            host.close()
            out, err = p.communicate(timeout=5)
            self.assertNotEqual(p.returncode, 0)
            rows = [json.loads(x) for x in (Path(directory) / 'unconnected.jsonl').read_text().splitlines()]
            self.assertEqual([r['result'] for r in rows], ['UNKNOWN', 'UNKNOWN'])

    def test_reproduce_invalid_deadline_does_not_consume_owned_stream(self):
        host, peer = socket.socketpair()
        try:
            with self.assertRaises(ValueError):
                measure.measure(host, float('nan'))
            self.assertGreaterEqual(host.fileno(), 0)
            peer.settimeout(.03)
            with self.assertRaises(TimeoutError):
                peer.recv(1)
        finally:
            host.close(); peer.close()

    def test_reproduce_preflight_failure_leaves_fd_open_in_process(self):
        host, peer = socket.socketpair()
        try:
            argv = ['measure.py','--execute','--fd',str(host.fileno()),'--evidence',str(HERE/'evidence/uncreated.jsonl')]
            with patch.object(sys, 'argv', argv), patch.object(measure, 'check_inputs', side_effect=ValueError('changed pin')):
                with self.assertRaisesRegex(ValueError, 'changed pin'):
                    measure.main()
            peer.settimeout(.03)
            with self.assertRaises(TimeoutError):
                peer.recv(1)
            self.assertFalse((HERE/'evidence/uncreated.jsonl').exists())
        finally:
            host.close(); peer.close()

if __name__ == '__main__':
    suite = unittest.TestSuite([
        unittest.defaultTestLoader.loadTestsFromModule(test_measure),
        unittest.defaultTestLoader.loadTestsFromTestCase(IndependentTests)])
    run = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(0 if run.wasSuccessful() else 1)
