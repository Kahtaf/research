#!/usr/bin/env python3
import hashlib
import io
import struct
import unittest
from audit_restore_source import parse_transfer, payload_hashes, BLOCK

class RestoreSourceTests(unittest.TestCase):
    GOOD = b'4\n3\n0\n0\nnew 4,0,1,3,4\nzero 2,1,2\nerase 2,2,3\n'

    def test_binary_stream_and_discard_semantics(self):
        segments, size = parse_transfer(self.GOOD, 4)
        first = bytes(range(256)) * 16
        last = b'\xff\x00\r\n' * 1024
        result = payload_hashes(segments, io.BytesIO(first + last))
        self.assertEqual(size, 2 * BLOCK)
        self.assertEqual(result['new_dat_bytes_read'], size)
        self.assertEqual(result['canonical_zero_discard_sha256'],
                         hashlib.sha256(first + bytes(2 * BLOCK) + last).hexdigest())
        defined = (struct.pack('<QQ', 0, 1) + first + struct.pack('<QQ', 1, 2) +
                   bytes(BLOCK) + struct.pack('<QQ', 3, 4) + last)
        self.assertEqual(result['defined_ranges_sha256'], hashlib.sha256(defined).hexdigest())

    def test_reject_incomplete_overlapping_or_out_of_bounds_ranges(self):
        for old, new in [(b'erase 2,2,3\n', b''), (b'erase 2,2,3', b'erase 2,1,3'),
                         (b'new 4,0,1,3,4', b'new 4,0,1,3,5'),
                         (b'new 4,0,1,3,4', b'new 3,0,1,3,4')]:
            with self.subTest(new=new), self.assertRaises(ValueError):
                parse_transfer(self.GOOD.replace(old, new), 4)

    def test_reject_different_payload_semantics(self):
        for old, new in [(b'4\n3\n', b'3\n3\n'), (b'4\n3\n', b'4\n4\n'),
                         (b'new 4,0,1,3,4', b'move 4,0,1,3,4'),
                         (b'new 4,0,1,3,4', b'new 4,3,4,0,1')]:
            with self.subTest(new=new), self.assertRaises(ValueError):
                parse_transfer(self.GOOD.replace(old, new), 4)

    def test_reject_short_or_trailing_new_data(self):
        segments, size = parse_transfer(self.GOOD, 4)
        for amount in (size - 1, size + 1):
            with self.subTest(amount=amount), self.assertRaises(ValueError):
                payload_hashes(segments, io.BytesIO(bytes(amount)))

if __name__ == '__main__':
    unittest.main()
