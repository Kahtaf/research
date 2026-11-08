import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import socket
import stat
import struct
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'source'))
import worker
import sources
import source_client
import source_manifest
import build_manifest
import parent_remote
from pinned import client, manifest

C = worker.CHUNK

def sha(data):
    return hashlib.sha256(data).digest()


def chunk_hashes(data):
    return b''.join(sha(data[i:i+C]) for i in range(0, len(data), C))


def binary_manifest(images):
    b = b'ASUSR002' + struct.pack('<II', 2, len(images)) + b'I' * 96
    for i, data in enumerate(images):
        chunks = chunk_hashes(data)
        b += struct.pack('<IIQ', i, 26 if i == 4 else 9 if i % 2 else 25, len(data))
        b += sha(data) + struct.pack('<I', len(chunks)//32) + chunks
    return b


class SourceThread:
    """In-process mock pipes only. Never executes a target or SSH subprocess."""
    def __init__(self, profile, handler=None):
        a, b = socket.socketpair()
        a.settimeout(5)
        b.settimeout(5)
        self.stdin = a.makefile('wb', buffering=0)
        self.stdout = a.makefile('rb', buffering=0)
        a.close()
        self.error = None
        def run():
            try:
                with b, b.makefile('rb', buffering=0) as reader, b.makefile('wb', buffering=0) as writer:
                    (handler or worker.serve)(profile, reader, writer)
            except (EOFError, BrokenPipeError, ConnectionResetError):
                pass
            except BaseException as e:
                self.error = e
        self.thread = threading.Thread(target=run, daemon=True)
        self.thread.start()

    def wait(self, timeout=None):
        self.thread.join(timeout)
        if self.thread.is_alive():
            raise TimeoutError('mock source did not close')
        return 0


class MockTarget:
    """Explicit in-memory RSC1 fixture. No device node, daemon or target Popen.
    Retains actual bytes across disconnected sessions; rejects concurrent writer,
    forged selection, invalid SKIP, role ordering and uncertain inverse changes.
    """
    def __init__(self, images):
        self.images = images
        self.manifest = binary_manifest(images)
        self.p10 = sha(b'fixed p10')
        self.parts = {25: bytearray(images[0]), 9: bytearray(images[1])}
        if len(images) == 5:
            self.parts[26] = bytearray(b'?' * len(images[4]))
        self.pending = None
        self.committed = set()
        self.writer = False
        self.ops = []
        self.sessions = []
        self.lock = threading.Lock()

    def connect(self, fault=None, hook=None):
        a, b = socket.socketpair()
        a.setblocking(True)
        b.setblocking(True)
        errors = []
        def run():
            selected = None
            offset = 0
            index = 0
            active = False
            token = b'T' * 32
            try:
                with b:
                    while True:
                        magic, op, size = struct.unpack('<4sII', client.readn(b.fileno(), 12))
                        if magic != b'RSC1' or size > C:
                            raise ValueError('frame')
                        data = client.readn(b.fileno(), size)
                        self.ops.append(op)
                        if op == 1:
                            if self.writer:
                                raise ValueError('busy')
                            client.send(b.fileno(), 0x81, b'protocol=1 writer=idle armed=1')
                        elif op in (2, 8):
                            if len(data) != (104 if op == 8 else 68):
                                raise ValueError('reconcile size')
                            if data[:32] != sha(self.manifest) or data[32:64] != self.p10:
                                raise ValueError('manifest/p10')
                            selected = struct.unpack_from('<I', data, 64)[0]
                            row = client.parse(self.manifest)[selected]
                            if self.writer:
                                raise ValueError('writer')
                            if self.pending is not None and self.pending != selected:
                                if op != 8 or selected > 1 or struct.unpack_from('<I', data, 68)[0] != self.pending or data[72:] != row['full']:
                                    raise ValueError('explicit inverse required')
                            if selected % 2 and selected - 1 not in self.committed:
                                raise ValueError('SYSTEM must precede BOOT')
                            if selected == 4 and 2 not in self.committed:
                                raise ValueError('SYSTEM must precede data')
                            if selected == 3 and len(self.images) == 5 and 4 not in self.committed:
                                raise ValueError('data must precede BOOT')
                            actual = self.parts[row['part']]
                            same = bytes(sha(actual[i:i+C]) == row['chunks'][(i//C)*32:(i//C+1)*32]
                                         for i in range(0, row['size'], C))
                            client.send(b.fileno(), 0x82, token + same)
                        elif op == 3:
                            if selected is None or data != token:
                                raise ValueError('token')
                            with self.lock:
                                if self.writer:
                                    raise ValueError('one writer')
                                self.writer = True
                            active = True
                            self.pending = selected
                            client.send(b.fileno(), 0x83)
                            if hook:
                                hook('begin', 0)
                        elif op in (4, 7):
                            if not active:
                                raise ValueError('not active')
                            row = client.parse(self.manifest)[selected]
                            length = min(C, row['size'] - offset)
                            if length <= 0:
                                raise ValueError('chunk overflow')
                            actual = self.parts[row['part']]
                            expected = row['chunks'][index*32:(index+1)*32]
                            if op == 7:
                                if data or sha(actual[offset:offset+length]) != expected:
                                    raise ValueError('false skip')
                            else:
                                if len(data) != length or sha(data) != expected:
                                    raise ValueError('bad write')
                                actual[offset:offset+length] = data
                            if hook:
                                hook('chunk', index)
                            if fault == 'ack' and index == 0:
                                return
                            client.send(b.fileno(), 0x84, struct.pack('<II', index + (1 if fault == 'wrongack' else 0), op == 7))
                            offset += length
                            index += 1
                        elif op == 5:
                            row = client.parse(self.manifest)[selected]
                            if offset != row['size'] or sha(self.parts[row['part']]) != row['full']:
                                raise ValueError('whole readback')
                            client.send(b.fileno(), 0x85, b'X'*32 if fault == 'whole' else row['full'])
                        elif op == 9:
                            row = client.parse(self.manifest)[selected]
                            if data != row['full'] or sha(self.parts[row['part']]) != data:
                                raise ValueError('commit')
                            if fault == 'commit':
                                return
                            self.committed.add(selected)
                            self.pending = None
                            active = False
                            self.writer = False
                            client.send(b.fileno(), 0x89, data)
                        else:
                            raise ValueError('unexpected opcode')
            except (EOFError, ConnectionResetError, BrokenPipeError):
                pass
            except BaseException as e:
                errors.append(str(e))
                try:
                    client.send(b.fileno(), 255, str(e).encode())
                except OSError:
                    pass
            finally:
                if active:
                    self.writer = False
        thread = threading.Thread(target=run, daemon=True)
        thread.start()
        self.sessions.append((thread, errors))
        return a

    def join(self):
        for t, _ in self.sessions:
            t.join(5)
            if t.is_alive():
                raise RuntimeError('mock target still active')


class Fixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT/'artifacts', prefix='unit-')
        self.root = Path(self.temp.name).resolve()
        self.data = b'A'*C + bytes(C) + b'Z'*3584
        self.path = self.root/'raw'
        self.path.write_bytes(self.data)
        self.path.chmod(0o400)
        self.profile = self.make_profile(self.path, self.data, 0)
        self.opened = []

    def tearDown(self):
        for item in self.opened:
            item.close()
        self.temp.cleanup()

    def make_profile(self, path, data, role):
        return dict(role=role, path=str(path), size=len(data), sha256=sha(data).hex(),
                    uid=os.getuid(), gid=os.getgid(), mode=0o400, nlink=1,
                    chunk_bytes=C, count=(len(data)+C-1)//C,
                    chunks_sha256=sha(chunk_hashes(data)).hex())

    def source(self, remote=False, data=None, role=0, handler=None):
        data = self.data if data is None else data
        path = self.root / ('source-' + str(len(self.opened)))
        path.write_bytes(data)
        path.chmod(0o400)
        profile = self.make_profile(path, data, role)
        if remote:
            with patch.object(sources, 'reference', return_value=(profile, chunk_hashes(data))), \
                 patch.object(sources.subprocess, 'Popen', side_effect=lambda *a, **kw: SourceThread(profile, handler)):
                result = sources.RemoteSource('userdata-pristine').open()
        else:
            result = sources.LocalSource(profile)
        self.opened.append(result)
        return result

    def mutate(self, path, data=b'X'):
        p = Path(path)
        p.chmod(0o600)
        with p.open('r+b') as f:
            f.write(data)
        p.chmod(0o400)

    def write(self, target, source, index=0, fault=None, hook=None, inverse=None, stop=None):
        prepared = source_client.prepare_source(target.manifest, index, source,
                                               sha(target.images[index]).hex(), stop)
        with (self.root / ('journal-' + str(len(target.sessions)))).open('x') as evidence:
            with target.connect(fault, hook) as sock:
                try:
                    source_client.write_image(sock.fileno(), target.manifest, target.p10, index,
                        source, sha(target.images[index]).hex(), evidence,
                        inverse_from=inverse, stop_after=stop, prepared=prepared)
                finally:
                    with contextlib.suppress(OSError):sock.shutdown(socket.SHUT_RDWR)
        target.join()

    def test_guards_symlink_ancestor_type_size_mode_owner_links(self):
        cases = ['symlink', 'ancestor', 'directory', 'fifo', 'size', 'mode', 'uid', 'gid', 'hardlink']
        for case in cases:
            with self.subTest(case=case):
                p = self.root/('guard-' + case)
                p.write_bytes(self.data)
                p.chmod(0o400)
                prof = self.make_profile(p, self.data, 0)
                if case == 'symlink':
                    p.unlink(); p.symlink_to(self.path)
                elif case == 'ancestor':
                    link = self.root/'alias'; link.symlink_to(self.root, target_is_directory=True)
                    prof['path'] = str(link/p.name)
                elif case == 'directory':
                    p.unlink(); p.mkdir()
                elif case == 'fifo':
                    p.unlink(); os.mkfifo(p, 0o400)
                elif case == 'size':
                    prof['size'] += 1
                elif case == 'mode':
                    p.chmod(0o600)
                elif case in ('uid', 'gid'):
                    prof[case] += 1
                elif case == 'hardlink':
                    os.link(p, self.root/'link')
                with self.assertRaises((ValueError, OSError)):
                    worker.HeldRaw(prof)

    def test_full_preflight_and_remote_chunk_zero_tail(self):
        for remote in (False, True):
            with self.subTest(remote=remote):
                s = self.source(remote=remote)
                self.assertEqual(s.preflight(), (sha(self.data), chunk_hashes(self.data)))
                self.assertEqual(s.read_chunk(0), b'A'*C)
                self.assertEqual(s.read_chunk(1), bytes(C))
                self.assertEqual(s.read_chunk(2), b'Z'*3584)
                s.close()

    def test_sparse_holes_are_materialized_zero_bytes(self):
        self.path.chmod(0o600)
        with self.path.open('wb') as f:
            f.write(b'A'*C); f.seek(C, 1); f.write(bytes(3584))
        self.path.chmod(0o400)
        data = b'A'*C + bytes(C+3584)
        p = self.make_profile(self.path, data, 0)
        source = sources.LocalSource(p)
        try:
            source.preflight()
            self.assertEqual(source.read_chunk(0), b'A'*C)
            self.assertEqual(source.read_chunk(1), bytes(C))
            self.assertEqual(source.read_chunk(2), bytes(3584))
        finally:
            source.close()

    def test_android_sparse_encoding_rejected(self):
        s = self.source(data=bytes.fromhex('3aff26ed')+b'A'*128)
        with self.assertRaisesRegex(ValueError, 'sparse'):
            s.preflight()

    def test_bad_full_or_chunk_hash_before_target(self):
        for key in ('sha256', 'chunks_sha256'):
            prof = dict(self.profile); prof[key] = '0'*64
            s = sources.LocalSource(prof)
            try:
                with self.assertRaisesRegex(ValueError, 'mismatch'):
                    s.preflight()
            finally:
                s.close()

    def test_held_fd_mutation_before_during_after_preflight(self):
        for when in ('before', 'during', 'after', 'replace', 'truncate'):
            with self.subTest(when=when):
                s = self.source()
                if when == 'before':
                    self.mutate(s.profile['path'])
                if when == 'during':
                    original = os.pread
                    def changed(fd, n, off):
                        data = original(fd, n, off)
                        self.mutate(s.profile['path'])
                        return data
                    with patch.object(worker.os, 'pread', side_effect=changed):
                        with self.assertRaisesRegex(ValueError, 'changed'):
                            s.preflight()
                    continue
                if when == 'before':
                    with self.assertRaisesRegex(ValueError, 'changed'):
                        s.preflight()
                    continue
                s.preflight()
                if when == 'replace':
                    path = Path(s.profile['path']); path.rename(path.with_suffix('.old'))
                    path.write_bytes(self.data); path.chmod(0o400)
                elif when == 'truncate':
                    path = Path(s.profile['path']); path.chmod(0o600)
                    with path.open('wb') as f:f.write(b'A')
                    path.chmod(0o400)
                else:
                    self.mutate(s.profile['path'])
                with self.assertRaisesRegex(ValueError, 'changed'):
                    s.read_chunk(0)
                with self.assertRaises(ValueError):
                    s.check()

    def test_short_pread_poisoned(self):
        s = self.source()
        with patch.object(worker.os, 'pread', return_value=b'x'):
            with self.assertRaisesRegex(ValueError, 'short'):
                s.preflight()
        with self.assertRaises(ValueError):s.check()

    def test_source_order_sample_and_request_bounds(self):
        s = self.source(remote=True)
        with self.assertRaises(ValueError):s.read_chunk(0)
        for i in (-1, 3, 1.5, True):
            with self.assertRaises(ValueError):s.read_chunk(i, sample=True)
        s.preflight()
        with self.assertRaises(ValueError):s.read_chunk(1)
        self.assertEqual(s.read_chunk(0), b'A'*C)
        with self.assertRaises(ValueError):s.read_chunk(0)
        with self.assertRaises((EOFError, ValueError)):
            s.exchange(2, worker.REQUEST.pack(1, C+1, C))
        s.close()
        s = self.source(remote=True)
        self.assertEqual(s.read_chunk(2, sample=True), b'Z'*3584)
        with self.assertRaises((EOFError, ValueError)):s.read_chunk(2, sample=True)

    def test_source_framing_short_magic_size_opcode(self):
        for encoded in (b'', b'SRC', worker.HEADER.pack(b'BAD!', 1, 0),
                        worker.HEADER.pack(b'SRC1', 1, C*2),
                        worker.HEADER.pack(b'SRC1', 2, 0),
                        worker.HEADER.pack(b'SRC1', 1, 5)+b'ab'):
            with self.subTest(encoded=encoded[:12]):
                with self.assertRaises((ValueError, EOFError)):
                    worker.receive(io.BytesIO(encoded), 1)
        class Fragments(io.BytesIO):
            def read(self, n=-1):return super().read(min(n, 1))
        self.assertEqual(worker.receive(Fragments(worker.HEADER.pack(b'SRC1', 1, 3)+b'abc'), 1), (1,b'abc'))

    def test_host_rejects_corrupt_truncated_wrong_index_position_digest(self):
        for change in ('short', 'index', 'offset', 'length', 'digest', 'data', 'drop'):
            with self.subTest(change=change):
                s = self.source(remote=True)
                s.preflight()
                valid = worker.REPLY.pack(0, 0, C, sha(self.data[:C])) + self.data[:C]
                if change == 'short':reply = valid[:-1]
                elif change == 'index':reply = worker.REPLY.pack(1, 0, C, sha(self.data[:C]))+self.data[:C]
                elif change == 'offset':reply = worker.REPLY.pack(0, 1, C, sha(self.data[:C]))+self.data[:C]
                elif change == 'length':reply = worker.REPLY.pack(0, 0, C-1, sha(self.data[:C]))+self.data[:C]
                elif change == 'digest':reply = worker.REPLY.pack(0, 0, C, b'0'*32)+self.data[:C]
                elif change == 'data':reply = valid[:-1]+b'?'
                else:reply = None
                with patch.object(s, 'exchange', side_effect=EOFError('drop') if reply is None else None, return_value=reply):
                    with self.assertRaises((ValueError, EOFError)):s.read_chunk(0)
                self.assertEqual(s.next_index, 0)
                s.close()

    def test_complete_write_skip_tail_and_commit_over_real_mock_streams(self):
        target = MockTarget([self.data, b'B'*4096])
        target.parts[25][:C] = b'?'*C
        s = self.source(remote=True)
        self.write(target, s)
        self.assertEqual(bytes(target.parts[25]), self.data)
        self.assertEqual(target.ops, [1, 2, 3, 4, 7, 7, 5, 9])
        self.assertEqual(target.committed, {0})
        self.assertLess((self.root/'journal-0').stat().st_size, 4096)

    def test_lost_ack_no_resend_explicit_later_idle_reconciliation(self):
        target = MockTarget([self.data, b'B'*4096])
        target.parts[25][:] = b'?'*len(self.data)
        s = self.source(remote=True)
        with self.assertRaises(EOFError):self.write(target, s, fault='ack')
        target.join()
        self.assertEqual(target.ops, [1, 2, 3, 4])
        self.assertEqual(target.parts[25][:C], self.data[:C])
        with self.assertRaises((ValueError, EOFError)):s.read_chunk(1)
        s2 = self.source(remote=True)
        self.write(target, s2)
        self.assertEqual(target.ops[4:7], [1, 2, 3])
        self.assertEqual(target.ops[7:], [7, 4, 4, 5, 9])
        self.assertEqual(target.committed, {0})

    def test_inverse_requires_explicit_original_selection(self):
        install = b'T'*C + bytes(C) + b'W'*3584
        target = MockTarget([self.data, b'B'*4096, install, b'N'*4096])
        with self.assertRaises(EOFError):self.write(target, self.source(remote=True, data=install, role=2), index=2, fault='ack')
        target.join()
        with self.assertRaises((EOFError, RuntimeError)):self.write(target, self.source(), index=0)
        target.join()
        self.write(target, self.source(remote=True), inverse=2)
        self.assertEqual(bytes(target.parts[25]), self.data)
        self.assertIn(8, target.ops)
        self.assertEqual(target.pending, None)

    def test_source_mutation_after_begin_or_after_one_ack_no_bad_send(self):
        for point in ('begin', 'chunk'):
            with self.subTest(point=point):
                target = MockTarget([self.data, b'B'*4096])
                target.parts[25][:] = b'?'*len(self.data)
                s = self.source(remote=True)
                def hook(event, index):
                    if event == point and index == 0:self.mutate(s.profile['path'])
                with self.assertRaises((EOFError, ValueError)):self.write(target, s, hook=hook)
                target.join()
                self.assertEqual(target.ops.count(4), 0 if point == 'begin' else 1)
                self.assertNotIn(5, target.ops)
                self.assertNotIn(9, target.ops)
                (self.root/'journal-0').unlink()

    def test_mutation_after_preflight_before_target_sends_nothing(self):
        target = MockTarget([self.data, b'B'*4096]);s=self.source(remote=True)
        prepared = source_client.prepare_source(target.manifest, 0, s, sha(self.data).hex())
        self.mutate(s.profile['path'])
        with (self.root/'journal').open('x') as evidence:
            with patch.object(source_client, 'status', side_effect=AssertionError('target touched')):
                with self.assertRaises((ValueError, EOFError)):
                    source_client.write_image(-1,target.manifest,target.p10,0,s,sha(self.data).hex(),evidence,prepared=prepared)

    def test_lost_commit_bad_whole_and_wrongack_never_claim_success(self):
        for fault in ('commit', 'whole', 'wrongack'):
            with self.subTest(fault=fault):
                target = MockTarget([self.data, b'B'*4096])
                with self.assertRaises((EOFError, ValueError)):
                    self.write(target, self.source(remote=True), fault=fault)
                target.join()
                log=(self.root/'journal-0').read_text()
                self.assertNotIn('whole_partition_verified',log)
                (self.root/'journal-0').unlink()
                self.assertNotIn(0,target.committed)
                if fault != 'commit':self.assertNotIn(9,target.ops)

    def test_partial_trial_stops_and_requires_fresh_session(self):
        target=MockTarget([self.data,b'B'*4096]);s=self.source(remote=True)
        self.write(target,s,stop=1)
        self.assertEqual(target.ops,[1,2,3,7])
        self.assertEqual(target.pending,0)
        self.assertIn('reconciliation_required', (self.root/'journal-0').read_text())
        with self.assertRaises((ValueError,EOFError)):s.preflight()

    def test_role_size_hash_manifest_and_prepared_binding(self):
        target=MockTarget([self.data,b'B'*4096])
        for index,digest in ((1,sha(self.data).hex()),(0,'0'*64),(3,sha(self.data).hex())):
            with self.assertRaises(ValueError):
                source_client.prepare_source(target.manifest,index,self.source(),digest)
        s=self.source();prepared=source_client.prepare_source(target.manifest,0,s,sha(self.data).hex())
        with (self.root/'journal').open('x') as e:
            with patch.object(source_client,'status',side_effect=AssertionError('target touched')):
                with self.assertRaises(ValueError):
                    source_client.write_image(-1,target.manifest,target.p10,0,self.source(),sha(self.data).hex(),e,prepared=prepared)

    def test_default_plan_never_starts_any_process(self):
        with patch.object(sys,'argv',['parent_remote.py','write']), \
             patch.object(parent_remote.subprocess,'Popen',side_effect=AssertionError('Popen forbidden')), \
             patch.object(parent_remote.subprocess,'run',side_effect=AssertionError('run forbidden')), \
             contextlib.redirect_stdout(io.StringIO()) as out:
            parent_remote.main()
        self.assertIn('PLAN_ONLY',out.getvalue())

    def test_unknown_profile_no_ssh_or_local_unbound_path(self):
        with patch.object(sources.subprocess,'Popen',side_effect=AssertionError('Popen forbidden')):
            for key in ('install-system','../../etc/passwd','stock-system; id'):
                with self.assertRaises((ValueError,KeyError)):sources.RemoteSource(key)
            with self.assertRaises(ValueError):sources.local_source(self.path)

    def test_approval_schema_and_role_order_cannot_be_bypassed(self):
        review=dict(cid_sha256='0'*64,primary_gpt_sha256='f87e70586706b06d029a2bc8521f1b8ae9176873cba1e5b4281cbaca816742ae',backup_gpt_sha256='2bf991125a74bf360d0cf4eb217df369ba2f78acf3dd312f26dc7695d2f31784',images={'original_system':{'path':'source://stock-system','sha256':'0'*64},'original_boot':{'path':'x','sha256':'0'*64}},approvals={})
        with patch.object(sources.subprocess,'Popen',side_effect=AssertionError('Popen forbidden')):
            with self.assertRaisesRegex(ValueError,'approvals'):build_manifest.build_review(review)
        review['approvals']={k:True for k in ['durable_original_system_backup','durable_original_boot_backup','durable_original_recovery_backup','independent_rescue_review']}
        for images in ({'original_boot':review['images']['original_boot'],'original_system':review['images']['original_system']}, {'original_system':review['images']['original_system']}, {**review['images'],'provision_userdata':{'path':'source://userdata-pristine','sha256':'0'*64}}):
            bad=dict(review,images=images)
            with patch.object(sources.subprocess,'Popen',side_effect=AssertionError('Popen forbidden')):
                with self.assertRaises(ValueError):build_manifest.build_review(bad)

    def test_source_receipt_not_approval_or_reusable_session(self):
        s=self.source(remote=True)
        with self.assertRaises(ValueError):s.receipt()
        s.preflight();receipt=s.receipt()
        self.assertFalse(receipt['target_authorized']);self.assertFalse(receipt['session_reuse'])
        s.close()
        with self.assertRaises(ValueError):s.receipt()

    def test_parent_preflight_before_features_or_target_creation(self):
        target = MockTarget([self.data, b'B'*4096])
        m = self.root/'manifest.bin'; m.write_bytes(target.manifest)
        contract = self.root/'contract.json'
        cb = json.dumps({'mode':'PARENT_APPROVED','armed':True,
                         'manifest_sha256':sha(target.manifest).hex(),
                         'p10_full_sha256':target.p10.hex()}).encode()
        contract.write_bytes(cb)
        fake_binary = self.root/'never-executed-adb'; fake_binary.write_bytes(b'QA ONLY')
        for corrupt in (True, False):
            with self.subTest(corrupt=corrupt):
                s = self.source()
                if corrupt:self.mutate(s.profile['path'])
                args=['parent_remote.py','write','--execute','--adb',str(fake_binary),
                      '--adb-sha256',sha(b'QA ONLY').hex(),'--transport-id','123',
                      '--contract',str(contract),'--contract-sha256',sha(cb).hex(),
                      '--manifest',str(m),'--image-index','0','--image',str(self.path),
                      '--image-sha256',sha(self.data).hex(),'--evidence',str(self.root/'parent.log')]
                feature_calls=[]
                def features(command, **kw):
                    self.assertTrue(s.verified)
                    feature_calls.append(command)
                    return type('Result',(),{'stdout':'NO_shell_v2'})()
                with patch.object(sys,'argv',args), \
                     patch.object(parent_remote,'local_source',return_value=s), \
                     patch.object(parent_remote.subprocess,'run',side_effect=features), \
                     patch.object(parent_remote.subprocess,'Popen',side_effect=AssertionError('actual target Popen forbidden')):
                    with self.assertRaises(ValueError):parent_remote.main()
                self.assertEqual(len(feature_calls),0 if corrupt else 1)
                if feature_calls:self.assertEqual(feature_calls[0],[str(fake_binary),'-t','123','features'])
                self.assertFalse((self.root/'parent.log').exists())

    def test_callback_manifest_binary_identical_for_2_4_5_role_schemas(self):
        import copy
        for count in (2,4,5):
            reviews={}
            digests={}
            for i,role in enumerate(manifest.ROLES[:count]):
                full = bytes.fromhex('7bb68511b1ade34d24c3e932da7260e6753fa87270bd8249a7218755a5df3316') if i==1 else sha(role.encode())
                size=manifest.GEOMETRY[26 if i==4 else 9 if i%2 else 25]
                chunks=[sha(str(i).encode())]*((size+C-1)//C)
                digests[role]=(full,chunks)
                reviews[role]={'path':role,'sha256':full.hex()}
            approvals={key:True for key in ['durable_original_system_backup','durable_original_boot_backup','durable_original_recovery_backup','independent_rescue_review']}
            if count==5:approvals.update({key:True for key in ['clean_internal_data','factory_wifi_bt_preserved_locally','p26_provision_reviewed']})
            review={'cid_sha256':'0'*64,'primary_gpt_sha256':'f87e70586706b06d029a2bc8521f1b8ae9176873cba1e5b4281cbaca816742ae','backup_gpt_sha256':'2bf991125a74bf360d0cf4eb217df369ba2f78acf3dd312f26dc7695d2f31784','images':reviews,'approvals':approvals}
            original_review=copy.deepcopy(review)
            digest=lambda path,size:digests[path]
            with patch.object(manifest,'digest_file',side_effect=digest):
                original=manifest.build(review)
            adapted=source_manifest.build(review,digest=digest)
            self.assertEqual(original,adapted)
            self.assertEqual(review,original_review)
            self.assertEqual(len(client.parse(adapted[0])),count)

    def test_source_drop_at_chunk_boundary_sends_no_bad_target_frame(self):
        target=MockTarget([self.data,b'B'*4096]);target.parts[25][:]=b'?'*len(self.data)
        s=self.source(remote=True)
        read=s.read_chunk
        def drop(index):
            if index==1:
                s.close()
                raise EOFError('injected source SSH loss')
            return read(index)
        with patch.object(s,'read_chunk',side_effect=drop):
            with self.assertRaises(EOFError):self.write(target,s)
        target.join()
        self.assertEqual(target.ops,[1,2,3,4])
        self.assertEqual(target.parts[25][:C],self.data[:C])
        self.assertEqual(target.parts[25][C:],b'?'*(len(self.data)-C))

    def test_bounded_journal_and_stderr(self):
        from journal import BoundedJournal,StderrCapture
        sink=io.StringIO();j=BoundedJournal(sink,4)
        j.write('abcd')
        with self.assertRaises(ValueError):j.write('e')
        self.assertEqual(sink.getvalue(),'abcd')
        out=io.BytesIO();capture=StderrCapture(io.BytesIO(b'X'*100000),out,64)
        capture.finish()
        self.assertEqual(len(out.getvalue()),64)

    def test_remote_preflight_whole_table_mismatch_poisoned(self):
        s=self.source(remote=True)
        with patch.object(s,'exchange',return_value=b'wrong'):
            with self.assertRaises(ValueError):s.preflight()
        self.assertTrue(s.dead)
        with self.assertRaises(ValueError):s.read_chunk(0)

    def test_mock_target_system_data_boot_order(self):
        install=b'T'*C+bytes(C)+b'Q'*3584
        userdata=b'D'*C+bytes(C+3584)
        target=MockTarget([self.data,b'B'*4096,install,b'N'*4096,userdata])
        with self.assertRaises((EOFError,RuntimeError)):
            self.write(target,self.source(data=b'N'*4096,role=3),index=3)
        target.join()
        self.write(target,self.source(data=install,role=2),index=2)
        with self.assertRaises((EOFError,RuntimeError)):
            self.write(target,self.source(data=b'N'*4096,role=3),index=3)
        target.join()
        self.write(target,self.source(remote=True,data=userdata,role=4),index=4)
        self.assertEqual(bytes(target.parts[26][-3584:]),bytes(3584))
        self.write(target,self.source(data=b'N'*4096,role=3),index=3)
        self.assertEqual(target.committed,{2,4,3})


if __name__=='__main__':
    unittest.main(verbosity=2)
