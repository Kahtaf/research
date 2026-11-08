import hashlib
import importlib.util
import io
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('prepare', ROOT / 'source/prepare.py')
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


class ShortReads(io.BytesIO):
    def read(self, count=-1):
        return super().read(min(count, 3) if count >= 0 else 3)


class PrepareTests(unittest.TestCase):
    def test_reconstruct_materializes_zero_and_erase(self):
        segments = [(0, 1, 'new', 0), (1, 2, 'zero', None), (2, 3, 'erase', None), (3, 4, 'new', 4096)]
        expected = b'a' * 4096 + bytes(8192) + b'b' * 4096
        output = io.BytesIO()
        self.assertEqual(p.reconstruct(segments, ShortReads(b'a' * 4096 + b'b' * 4096), output, len(expected)), p.digest(expected))
        self.assertEqual(output.getvalue(), expected)

    def test_invalid_maps_refused_before_writes(self):
        for segments in [[(1, 2, 'new', 0)], [(0, 2, 'new', 0), (1, 2, 'zero', None)],
                         [(0, 1, 'new', 3)], [(0, 2, 'zero', 0)], [(0, 2, 'move', None)],
                         [(0, 3, 'zero', None)], [(0, 1, 'zero', None)]]:
            with self.subTest(segments=segments), self.assertRaises(ValueError):
                p.reconstruct(segments, io.BytesIO(), io.BytesIO(), 8192)

    def test_truncated_or_trailing_payload_refused(self):
        for data in [b'x' * 4095, b'x' * 4097]:
            with self.subTest(size=len(data)), self.assertRaises(ValueError):
                p.reconstruct([(0, 1, 'new', 0)], io.BytesIO(data), io.BytesIO(), 4096)

    def test_short_writes_refused(self):
        class BrokenOutput:
            def write(self, data):
                return len(data) - 1
        with self.assertRaises(ValueError):
            p.reconstruct([(0, 1, 'zero', None)], io.BytesIO(), BrokenOutput(), 4096)

    def test_independent_chunks_catch_corruption_and_bad_metadata(self):
        data = b'a' * 4096 + b'b' * 4096
        rows = []
        for i in range(2):
            h = p.digest(data[i * 4096:(i + 1) * 4096])
            rows.append(dict(index=i, offset=i * 4096, bytes=4096, remote_sha256=h, sha256_a=h, sha256_b=h))
        with tempfile.TemporaryDirectory(dir=ROOT / 'tests') as tmp:
            path = Path(tmp) / 'system.img'; path.write_bytes(data)
            self.assertEqual(p.verify_chunks(path, rows, len(data), p.digest(data))['verified_chunks'], 2)
            for changed in [[rows[0]], [rows[1], rows[0]], [dict(rows[0], sha256_b='bad'), rows[1]]]:
                with self.subTest(changed=changed), self.assertRaises(ValueError):
                    p.verify_chunks(path, changed, len(data), p.digest(data))
            path.write_bytes(data[:-1] + b'c')
            with self.assertRaises(ValueError):
                p.verify_chunks(path, rows, len(data), p.digest(data))

    def test_actual_pinned_inputs_load(self):
        _, backup, originals = p.load_inputs()
        self.assertEqual(len(backup['chunks']), 112)
        self.assertEqual(p.digest(originals['boot']), p.BOOT_SHA)
        self.assertEqual(p.digest(originals['recovery']), p.RECOVERY_SHA)

    def test_plan_only_by_default(self):
        result = subprocess.run(['python3', '-B', str(ROOT / 'source/prepare.py')], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn('PLAN_ONLY', result.stdout)


if __name__ == '__main__':
    unittest.main()
