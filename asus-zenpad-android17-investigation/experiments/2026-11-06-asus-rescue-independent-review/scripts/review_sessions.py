"""Small Linux ordinary-file/session tests, never a production block backend.

Runs only in the separate review fixture. Original adapter and source are copied
byte-for-byte; extra tests below exercise the included actual session function.
"""
import hashlib
import json
import os
import socket
import struct
import sys
import time
import unittest
from pathlib import Path

R = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(R/'source'), str(R/'tests')]
import client
import test_adapters as a

class Review(a.Adapter):
    def test_zero_record_status_does_not_validate_hardware_identity(self):
        self.manifest = self.manifest[:12]+struct.pack('<I',0)+self.manifest[16:112]
        (self.root/'rescue.manifest').write_bytes(self.manifest)
        (self.root/'sys/class/block/mmcblk0/device/cid').write_bytes(b'BAD-CID')
        (self.root/'dev/block/mmcblk0').unlink()
        self.start()
        with self.connect() as s:
            self.assertIn('armed=0', client.status(s.fileno()))
            client.send(s.fileno(),6,struct.pack('<II',25,0))
            self.assertRaises(RuntimeError,client.receive,s.fileno(),0x86)

    def test_op6_succeeds_without_p10_pin_after_recovery_changed(self):
        self.start()
        (self.root/'dev/block/mmcblk0p10').write_bytes(b'Q'+self.recovery[1:])
        with self.connect() as s:
            client.send(s.fileno(),6,struct.pack('<II',25,3))
            digest=client.receive(s.fileno(),0x86); data=client.receive(s.fileno(),0x87)
            self.assertEqual(digest,a.h(data)); self.assertEqual(data,self.original[0][3*a.C:])
        with self.connect() as s:
            self.assertRaises(RuntimeError,self.recon,s,2)

    def test_one_committed_image_closes_connection(self):
        self.start()
        with self.connect() as s:
            self.complete(s,0)
            self.assertEqual(s.recv(1),b'')
        with self.connect() as s:
            self.assertIn('uncertain_image=-1',client.status(s.fileno()))
            self.complete(s,1)

    def test_reconcile_then_readback_same_connection_is_rejected(self):
        self.start()
        with self.connect() as s:
            self.recon(s,0)
            client.send(s.fileno(),6,struct.pack('<II',25,0))
            self.assertRaises(RuntimeError,client.receive,s.fileno(),0x86)

    def test_lost_commit_receipt_does_not_always_leave_daemon_frozen(self):
        # Keep client connected long enough for the kernel to accept 0x89, but
        # intentionally never read it. Peer acceptance != host receipt.
        self.start()
        s=self.connect(); same=self.begin(s,0)
        for _ in same:
            client.send(s.fileno(),7);client.receive(s.fileno(),0x84)
        client.send(s.fileno(),5);digest=client.receive(s.fileno(),0x85)
        client.send(s.fileno(),9,digest)
        with self.connect() as later:
            status=client.status(later.fileno())
            self.assertIn('state=IDLE',status)
            self.assertIn('uncertain_image=-1',status)
        s.close()

    def test_slow_trickle_exceeds_receive_timeout_but_frame_succeeds(self):
        # Original test server has a 2-second socket receive timeout. Three
        # progress-making reads over >2 seconds show no total frame deadline.
        self.start()
        with self.connect() as s:
            msg=b'RSC1'+struct.pack('<II',1,0)
            started=time.monotonic()
            s.sendall(msg[:4]);time.sleep(1.1)
            s.sendall(msg[4:8]);time.sleep(1.1)
            s.sendall(msg[8:]);self.assertIn(b'writer=idle',client.receive(s.fileno(),0x81))
            self.assertGreater(time.monotonic()-started,2)

    def test_busy_frame_allows_no_second_writer_then_recovers_after_idle_timeout(self):
        self.start(); old=self.connect(); self.begin(old)
        old.sendall(b'RSC1'+struct.pack('<II',4,a.C)+self.install[0][:123])
        with self.connect() as new:
            new.settimeout(.15);client.send(new.fileno(),1)
            with self.assertRaises(socket.timeout):new.recv(12)
            new.setblocking(True)
            self.assertIn(b'uncertain_image=2',client.receive(new.fileno(),0x81))
        old.close()
        self.assertEqual((self.root/'dev/block/mmcblk0p25').read_bytes(),self.original[0])

    def test_status_reconcile_and_activation_same_connection(self):
        self.start()
        with self.connect() as s:
            self.assertIn('writer=idle',client.status(s.fileno()))
            token, same, _ = self.recon(s,0)
            client.send(s.fileno(),3,token);self.assertEqual(client.receive(s.fileno(),0x83),b'')
            for _ in same:
                client.send(s.fileno(),7);client.receive(s.fileno(),0x84)
            client.send(s.fileno(),5);digest=client.receive(s.fileno(),0x85)
            client.send(s.fileno(),9,digest);self.assertEqual(client.receive(s.fileno(),0x89),digest)

if __name__=='__main__':
    selected_original = [
        'test_binary_framing_fragmented_and_bounds',
        'test_partial_payload_disconnect_never_writes',
        'test_disconnect_reconcile_actual_hashes',
        'test_explicit_original_inverse_after_uncertain_install',
        'test_resume_rejects_changed_p10_pin_even_if_actual_matches',
        'test_faults_freeze',
        'test_full_readback_detects_changed_earlier_chunk',
        'test_optional_userdata_system_then_data_then_boot_and_zero_tail',
    ]
    suite = unittest.TestSuite([a.Adapter(n) for n in selected_original] +
                              [Review(n) for n in Review.__dict__ if n.startswith('test_')])
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    report={'passed':result.wasSuccessful(),'run':result.testsRun,
            'failures':len(result.failures),'errors':len(result.errors),
            'backend':'RESCUE_TEST ordinary files; synthetic small geometry; no SELinux/peer/physical descriptor proof',
            'fixture':str(R),'cpu_affinity':sorted(os.sched_getaffinity(0)),
            'source_sha256':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in sorted((R/'source').glob('*')) if p.is_file()}}
    (R/'evidence/session-tests.json').write_text(json.dumps(report,indent=2)+'\n')
    sys.exit(not result.wasSuccessful())
