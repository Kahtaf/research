#!/usr/bin/env python3
import hashlib
import io
import struct
import unittest
from audit_restore_source import BLOCK, parse_transfer
from prepare_comparison_manifest import comparison_digests


class ComparisonTests(unittest.TestCase):
    LIST = b'4\n4\n0\n0\nnew 4,0,1,4,6\nzero 2,1,2\nerase 2,2,4\n'

    def setUp(self):
        self.segments, self.new_size = parse_transfer(self.LIST, 6)
        self.first = bytes(range(256)) * 16
        self.last = b'\xff\x00\r\n' * 2048
        self.raw = self.first + bytes(3*BLOCK) + self.last

    def test_chunk_and_segment_boundaries_match_actual_bytes(self):
        result = comparison_digests(self.segments, io.BytesIO(self.first+self.last),
                                    6*BLOCK, chunk_bytes=2*BLOCK)
        self.assertEqual(result['canonical_zero_erase_sha256'], hashlib.sha256(self.raw).hexdigest())
        self.assertEqual([r['defined_bytes'] for r in result['chunks']], [2*BLOCK, 0, 2*BLOCK])
        for row in result['chunks']:
            data = self.raw[row['offset']:row['offset']+row['bytes']]
            self.assertEqual(row['canonical_zero_erase_sha256'], hashlib.sha256(data).hexdigest())
        self.assertEqual(result['chunks'][1]['defined_slices_sha256'], hashlib.sha256(b'').hexdigest())
        defined = struct.pack('<QQ',0,BLOCK)+self.first+struct.pack('<QQ',BLOCK,2*BLOCK)+bytes(BLOCK)
        self.assertEqual(result['chunks'][0]['defined_slices_sha256'], hashlib.sha256(defined).hexdigest())

    def test_single_segment_crossing_chunks_and_short_final_chunk(self):
        data = bytes(range(256))*48
        result = comparison_digests([(0,3,'new',0)],io.BytesIO(data),3*BLOCK,2*BLOCK)
        self.assertEqual([r['bytes'] for r in result['chunks']], [2*BLOCK,BLOCK])
        for row in result['chunks']:
            start,end=row['offset'],row['offset']+row['bytes']
            self.assertEqual(row['defined_slices_sha256'],hashlib.sha256(struct.pack('<QQ',start,end)+data[start:end]).hexdigest())

    def test_truncated_or_trailing_payload_never_emits_valid_result(self):
        for data in (bytes(self.new_size-1),bytes(self.new_size+1)):
            with self.assertRaises(ValueError):
                comparison_digests(self.segments,io.BytesIO(data),6*BLOCK,2*BLOCK)

    def test_invalid_maps_and_geometry_refused_before_source_reads(self):
        class NoRead:
            def read(self,*args):raise AssertionError('invalid map reached input')
        cases=[([(0,2,'new',0),(1,3,'zero',None)],3*BLOCK,2*BLOCK),
               ([(0,3,'new',1)],3*BLOCK,2*BLOCK),
               ([(0,3,'zero',0)],3*BLOCK,2*BLOCK),
               ([(0,4,'erase',None)],3*BLOCK,2*BLOCK),
               ([(0,2,'erase',None)],3*BLOCK,2*BLOCK),
               ([(0,3,'unknown',None)],3*BLOCK,2*BLOCK),
               ([(0,3,'new',0)],3*BLOCK,1)]
        for segments,total,chunk in cases:
            with self.subTest(segments=segments,total=total,chunk=chunk),self.assertRaises(ValueError):
                comparison_digests(segments,NoRead(),total,chunk)


if __name__ == '__main__':
    unittest.main()
