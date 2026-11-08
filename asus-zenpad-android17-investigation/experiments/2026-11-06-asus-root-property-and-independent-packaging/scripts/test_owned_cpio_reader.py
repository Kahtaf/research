"""Behavior checks for the exact legitimate repeated directory and rejections."""
from pathlib import Path
import importlib.util
import unittest

spec = importlib.util.spec_from_file_location('owned_bootformat', Path(__file__).with_name('owned_bootformat.py'))
reader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reader)

def record(name, mode, uid=0, value=b'', ino=1):
    encoded = name.encode() + b'\0'
    fields = [ino, mode, uid, 0, 1, 0, len(value), 0, 0, 0, 0, len(encoded), 0]
    header = b'070701' + ''.join(f'{v:08x}' for v in fields).encode()
    return reader.pad(header + encoded, 4) + reader.pad(value, 4)

def archive(*entries):
    return reader.pad(b''.join(entries) + record('TRAILER!!!', 0), 512)

class ReaderBehavior(unittest.TestCase):
    def test_matching_empty_dev_directory_has_one_logical_entry(self):
        data = archive(record('dev', 0o40755), record('dev', 0o40755, ino=2))
        self.assertEqual(reader.parse_cpio(data), {'dev': (0o40755, 0, 0, b'')})

    def test_conflicting_or_unreviewed_duplicates_rejected(self):
        cases = [
            (record('dev', 0o40755), record('dev', 0o40700)),
            (record('dev', 0o40755), record('dev', 0o40755, uid=1000)),
            (record('dev', 0o40755), record('dev', 0o40755, value=b'x')),
            (record('dev', 0o40755), record('dev', 0o40755), record('dev', 0o40755)),
            (record('init', 0o100755, value=b'elf'), record('init', 0o100755, value=b'elf')),
            (record('other', 0o40755), record('other', 0o40755)),
        ]
        for records in cases:
            with self.subTest(records=records):
                with self.assertRaises(AssertionError):
                    reader.parse_cpio(archive(*records))

if __name__ == '__main__':
    unittest.main()
