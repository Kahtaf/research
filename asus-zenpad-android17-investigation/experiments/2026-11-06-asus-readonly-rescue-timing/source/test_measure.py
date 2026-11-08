import json
import socket
import struct
import threading
import unittest
from unittest.mock import patch

import measure


def frame(opcode=0x82, body=b'x' * 32 + bytes([1]) * 16, magic=b'RSC1', length=None):
    return struct.pack('<4sII', magic, opcode, len(body) if length is None else length) + body


class FakeStream:
    def __init__(self, response):
        self.response = response
        self.requests = []
        self.closed = False

    def settimeout(self, seconds):
        self.timeout = seconds

    def sendall(self, request):
        self.requests.append(request)

    def recv(self, count):
        result, self.response = self.response[:min(count, 3)], self.response[min(count, 3):]
        return result

    def close(self):
        self.closed = True


class MeasurementTests(unittest.TestCase):
    def test_fixed_inputs_are_actual_unchanged_artifacts(self):
        measure.check_inputs()

    def test_real_unix_stream_fragmentation_and_no_activation(self):
        host, daemon = socket.socketpair()
        observed = {}

        def server():
            with daemon:
                daemon.settimeout(2)
                request = bytearray()
                while len(request) < 80:
                    request.extend(daemon.recv(80 - len(request)))
                observed['request'] = bytes(request)
                for byte in frame():
                    daemon.sendall(bytes([byte]))
                observed['after_reply'] = daemon.recv(80)

        thread = threading.Thread(target=server)
        thread.start()
        result = measure.measure(host, 2)
        thread.join(3)
        self.assertFalse(thread.is_alive())
        self.assertEqual(observed['request'], measure.REQUEST)
        self.assertEqual(observed['after_reply'], b'')
        self.assertEqual(result['result'], 'OBSERVED_MATCH')
        self.assertEqual(result['source_derived_partition_read_bytes'], 3_804_123_136)
        self.assertFalse(result['physical_GO'])
        self.assertNotIn('token', json.dumps(result))

    def test_only_opcode2_on_every_rejection(self):
        cases = [
            frame(opcode=0xff, body=b'guard failed'),
            frame(opcode=0x83),
            frame(magic=b'BAD!'),
            frame(length=1048577),
            frame(body=b'x' * 32 + bytes([1]) * 15),
            frame(body=b'x' * 32 + bytes([1]) * 15 + b'\x00'),
            frame(body=b'x' * 32 + bytes([1]) * 15 + b'\x02'),
            frame()[:-1],
            b'',
        ]
        for response in cases:
            with self.subTest(response=response):
                stream = FakeStream(response)
                with self.assertRaises((ValueError, EOFError)):
                    measure.measure(stream, 1)
                self.assertEqual(stream.requests, [measure.REQUEST])
                self.assertTrue(stream.closed)

    def test_fragmented_reply_cannot_reset_whole_deadline(self):
        stream = FakeStream(frame())
        ticks = iter([0, 0.1, 0.2, 0.4, 0.7, 1.01])
        with patch.object(measure.time, 'monotonic', side_effect=lambda: next(ticks)):
            with self.assertRaises(TimeoutError):
                measure.measure(stream, 1)
        self.assertEqual(stream.requests, [measure.REQUEST])
        self.assertTrue(stream.closed)

    def test_invalid_deadlines_send_nothing(self):
        for seconds in [0, -1, 601, float('inf'), float('nan')]:
            with self.subTest(seconds=seconds):
                stream = FakeStream(frame())
                with self.assertRaises(ValueError):
                    measure.measure(stream, seconds)
                self.assertEqual(stream.requests, [])
                self.assertTrue(stream.closed)
        host, peer = socket.socketpair()
        with peer:
            peer.settimeout(1)
            with self.assertRaises(ValueError):
                measure.measure(host, float('nan'))
            self.assertEqual(host.fileno(), -1)
            self.assertEqual(peer.recv(1), b'')

    def test_request_is_exact_original_boot_only(self):
        self.assertEqual(len(measure.REQUEST), 80)
        self.assertEqual(struct.unpack('<4sII', measure.REQUEST[:12]), (b'RSC1', 2, 68))
        self.assertEqual(measure.REQUEST[12:44].hex(), measure.MANIFEST)
        self.assertEqual(measure.REQUEST[44:76].hex(), measure.P10)
        self.assertEqual(struct.unpack('<I', measure.REQUEST[76:]), (1,))


if __name__ == '__main__':
    unittest.main(verbosity=2)
