"""Terminal framing remains bounded and truthful at every torn-write offset."""
from pathlib import Path
import json
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'source'))
from journal import BoundedJournal
from source_client import record_unknown

class Session:
    possible_partition_modification = True
    dead = False
    def poison(self):
        self.dead = True

def payload():
    return '\n' + json.dumps(dict(outcome='UNKNOWN', possible_partition_modification=True,
                                 automatic_retry=False)) + '\n'

class Boundaries(unittest.TestCase):
    def test_separator_is_included_in_capacity(self):
        for difference in (-1, 0):
            with self.subTest(capacity_difference=difference):
                with tempfile.TemporaryFile(mode='w+', dir=ROOT / 'evidence') as raw:
                    fd = Session()
                    journal = BoundedJournal(raw, len(payload().encode()) + difference)
                    self.assertEqual(record_unknown(fd, journal), difference == 0)
                    self.assertTrue(fd.dead)
                    raw.seek(0)
                    self.assertEqual(raw.read(), payload() if difference == 0 else '')

    def test_recovered_sink_frames_unknown_after_every_torn_prefix(self):
        for offset in range(len(payload())):
            with self.subTest(torn_at=offset):
                with tempfile.TemporaryFile(mode='w+', dir=ROOT / 'evidence') as raw:
                    class Sink:
                        pending = False
                        injected = False
                        def __getattr__(self, name):
                            return getattr(raw, name)
                        def write(self, text):
                            if self.pending:
                                self.pending = False
                                self.injected = True
                                raise OSError('one recoverable continuation fault')
                            if not self.injected:
                                if offset == 0:
                                    self.injected = True
                                    raise OSError('one recoverable initial fault')
                                self.pending = True
                                return raw.write(text[:offset])
                            return raw.write(text)
                    fd = Session()
                    journal = BoundedJournal(Sink(), 4096)
                    self.assertFalse(record_unknown(fd, journal))
                    self.assertTrue(fd.dead)
                    self.assertTrue(record_unknown(fd, journal))
                    self.assertTrue(fd.dead)
                    raw.seek(0)
                    lines = raw.read().splitlines()
                    self.assertEqual(json.loads(lines[-1]), json.loads(payload()))

if __name__ == '__main__':
    unittest.main(verbosity=2)
