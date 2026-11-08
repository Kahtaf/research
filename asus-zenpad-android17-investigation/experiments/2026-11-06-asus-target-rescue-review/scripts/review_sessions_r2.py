"""Correct only the review harness's nonblocking os.read mistake; retain r1.

Python socket.settimeout() puts the fd into nonblocking mode, whereas the
delivered client deliberately uses blocking os.read(). Restore blocking mode
after the negative timed recv. Run only the previously errored case.
"""
import json
import socket
import struct
import unittest
from pathlib import Path
import review_sessions as r1

class Corrected(r1.Review):
    def test_busy_frame_allows_no_second_writer_then_recovers_after_idle_timeout(self):
        self.start(); old=self.connect(); self.begin(old)
        try:
            old.sendall(b'RSC1'+struct.pack('<II',4,r1.a.C)+self.install[0][:123])
            with self.connect() as new:
                new.settimeout(.15);r1.client.send(new.fileno(),1)
                with self.assertRaises(socket.timeout):new.recv(12)
                new.setblocking(True)
                self.assertIn(b'uncertain_image=2',r1.client.receive(new.fileno(),0x81))
            self.assertEqual((self.root/'dev/block/mmcblk0p25').read_bytes(),self.original[0])
        finally:
            old.close()

result=unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite([
    Corrected('test_busy_frame_allows_no_second_writer_then_recovers_after_idle_timeout')]))
(r1.R/'evidence/session-tests-r2.json').write_text(json.dumps({
    'passed':result.wasSuccessful(),'run':result.testsRun,
    'reason':'corrected review harness settimeout/nonblocking FD mismatch only; original source untouched',
    'r1_preserved':True},indent=2)+'\n')
raise SystemExit(not result.wasSuccessful())
