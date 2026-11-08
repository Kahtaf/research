"""Offline fixtures only: never invoke ADB, root helper, SSH, VM or cloud APIs."""
import contextlib
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import tempfile
import tracemalloc
import unittest
from unittest.mock import patch

SPIKE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SPIKE/'source'))
import policy as p
import stock_system_backup as c
import remote_worker as r
import health as health
import continuation as cont

RUN = '20261106T180000Z-0123456789abcdef'
OBSERVATIONS = []
CODE_HASHES = {n: 'a'*64 for n in p.SOURCE_NAMES}
OLD = '20261106T155844Z-80cb7ab425df604b'

def fixture_input(payload):
    _, offset, length = p.chunk_layout()[0]
    digest = p.sha(payload[:length])
    row = dict(index=0, offset=offset, bytes=length, sha256_a=digest, sha256_b=digest, remote_sha256=digest,
               source_capture=dict(run=OLD, transport=dict(kind='adb-usb', serial=p.SERIAL), source_code_sha256=CODE_HASHES,
                                   helper_sha256='b'*64, root_binary_sha256=c.ROOT_BINARY_HASH, receipt_sha256='c'*64))
    r.dispatch(dict(operation='begin', run=OLD), io.BytesIO())
    r.dispatch(dict(operation='put', run=OLD, index=0, bytes=length, sha256=digest), io.BytesIO(payload[:length]))
    return dict(source_run=OLD, chunks=[row])


@contextlib.contextmanager
def small_geometry(size=3584, chunk=1024):
    layout = [(i, o, min(chunk, size-o)) for i, o in enumerate(range(0, size, chunk))]
    with contextlib.ExitStack() as stack:
        for module in (p, c, r):
            stack.enter_context(patch.object(module, 'SIZE', size))
            stack.enter_context(patch.object(module, 'CHUNK', chunk))
            stack.enter_context(patch.object(module, 'chunk_layout', return_value=layout))
        yield layout


class ByteDevice:
    def __init__(self, data, fault=None):
        self.data, self.fault = data, fault
        self.staged = {}
        self.calls = []
        self.closed = False
        self.clean_count = 0
    def setup(self):
        self.calls.append('setup')
        if self.fault == 'collision':
            raise p.Stop('existing stage')
    def stage(self, label, offset, length):
        self.calls.append(('read', label, offset, length))
        b = self.data[offset:offset+length]
        if self.fault == 'source_change' and label == 'b':
            b = bytes([b[0]^1])+b[1:]
        if self.fault == 'truncated_source' and label == 'a':
            b = b[:-1]
        self.staged[label] = b
    def binary(self, label, length, consume):
        self.calls.append(('binary', label))
        if self.fault == 'transport_loss':
            raise p.Stop('uncertain binary channel')
        for offset in range(0, len(self.staged[label]), 73):
            consume(self.staged[label][offset:offset+73])
    def clean_chunk(self):
        self.calls.append('clean')
        if self.fault == 'cleanup':
            raise p.Stop('cleanup failed')
        self.staged.clear()
        self.clean_count += 1
    def finish(self):
        self.calls.append('finish')
        self.closed = True


class FilesystemRemote:
    """Real remote worker, isolated fixture filesystem; no network process."""
    def __init__(self, fault=None):
        self.fault, self.calls = fault, []
    def call(self, operation, **fields):
        self.calls.append(operation)
        if self.fault == operation:
            raise p.Stop('lost SSH completion')
        return r.dispatch(dict(operation=operation, run=RUN, **fields), io.BytesIO())
    def put(self, index, path, length, digest):
        self.calls.append('put')
        if self.fault == 'put':
            # Remote may receive bytes, but lost acknowledgment must stop coordinator.
            with path.open('rb') as f:
                r.dispatch(dict(operation='put', run=RUN, index=index, bytes=length, sha256=digest), f)
            raise p.Stop('lost upload acknowledgement')
        with path.open('rb') as f:
            result = r.dispatch(dict(operation='put', run=RUN, index=index, bytes=length, sha256=digest), f)
        return result['sha256']


class BackupTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='offline-', dir=SPIKE/'tests')
        self.root = Path(self.tmp.name).resolve()
        self.local = self.root/'local'
        self.local.mkdir(mode=0o700)
        self.remote = self.root/'remote'
        self.patch = patch.object(r, 'REMOTE_BASE', self.remote)
        self.patch.start()
        self.journal = c.Journal(self.local)
        # Payload exercises NUL, CRLF, non-UTF8 and all byte values across boundaries.
        self.payload = (bytes(range(256))+b'\x00\r\n\xff\x80')*14
        self.payload = self.payload[:3584]
    def tearDown(self):
        self.patch.stop()
        self.tmp.cleanup()
    def transfer(self, device_fault=None, remote_fault=None):
        d, remote = ByteDevice(self.payload, device_fault), FilesystemRemote(remote_fault)
        with small_geometry():
            result = c.transfer(RUN, self.local, d, remote, self.journal, CODE_HASHES, fixture_input(self.payload))
        return result, d, remote
    def test_full_binary_backup_published_and_verified(self):
        result, d, remote = self.transfer()
        image = self.remote/RUN/'system.img'
        self.assertEqual(image.read_bytes(), self.payload)
        self.assertEqual(result['sha256'], hashlib.sha256(self.payload).hexdigest())
        self.assertEqual(d.clean_count, 3)
        self.assertTrue(d.closed)
        self.assertFalse((self.local/'chunk.bin').exists())
        self.assertTrue((self.local/'COMPLETE.json').is_file())
        m = json.loads((self.local/'manifest.json').read_bytes())
        self.assertEqual(m['bytes'], len(self.payload))
        self.assertEqual(m['assembled_sha256'], p.sha(self.payload))
        self.assertNotIn('source_sha256_a', m)
        self.assertNotIn('source_sha256_b', m)
        self.assertEqual(m['schema'], 2)
        self.assertEqual(m['source_code_sha256'], CODE_HASHES)
        self.assertEqual(m['transport'], dict(kind='adb-tcp', endpoint='IP_REDACTED:5555', secure_adb='1'))
        self.assertEqual(m['target']['serial'], 'DEVICE_SERIAL_REDACTED')
        self.assertEqual(m['helper_sha256'], c.HELPER_HASH)
        self.assertEqual(m['root_binary_sha256'], c.ROOT_BINARY_HASH)
        self.assertEqual(remote.calls[-2:], ['finalize', 'verify'])
        for f in (self.remote/RUN).iterdir():
            self.assertEqual(f.stat().st_mode & 0o777, 0o600)
        OBSERVATIONS.append(dict(case='full_binary_fixture', bytes=len(self.payload), chunks=4,
                                 sha256=result['sha256'], remote_readback=True, hardware=False))
    def test_failures_preserve_stage_and_never_complete(self):
        for device_fault, remote_fault in [('source_change', None), ('truncated_source', None),
                ('transport_loss', None), ('cleanup', None), ('collision', None),
                (None, 'put'), (None, 'finalize'), (None, 'verify')]:
            with self.subTest(device=device_fault, remote=remote_fault):
                # Each attempt uses a genuinely isolated directory and worker store.
                case = self.root/(str(device_fault)+'-'+str(remote_fault))
                case.mkdir(mode=0o700)
                d, remote = ByteDevice(self.payload, device_fault), FilesystemRemote(remote_fault)
                with patch.object(r, 'REMOTE_BASE', case/'remote'), small_geometry():
                    with self.assertRaises(p.Stop):
                        c.transfer(RUN, case, d, remote, c.Journal(case), CODE_HASHES, fixture_input(self.payload))
                self.assertFalse((case/'COMPLETE.json').exists())
                if device_fault in ('source_change', 'truncated_source', 'transport_loss') or remote_fault == 'put':
                    self.assertEqual(d.clean_count, 0)
                    self.assertTrue((case/'chunk.bin').exists())
                if remote_fault != 'verify':
                    self.assertFalse((case/'remote'/RUN/'READY.json').exists())
                if remote_fault == 'verify':
                    # Publication may already exist; host must still refuse completion.
                    self.assertTrue((case/'remote'/RUN/'READY.json').exists())
                OBSERVATIONS.append(dict(case=str(device_fault)+'-'+str(remote_fault), complete=False, retry=False))
    def test_remote_collision_cannot_overwrite(self):
        result, _, _ = self.transfer()
        old = (self.remote/RUN/'system.img').read_bytes()
        with self.assertRaises(p.Stop):
            r.dispatch(dict(operation='begin', run=RUN), io.BytesIO())
        self.assertEqual(old, (self.remote/RUN/'system.img').read_bytes())
    def test_remote_symlink_and_mode_rejected(self):
        other = self.root/'other'
        other.mkdir(mode=0o700)
        self.remote.symlink_to(other, target_is_directory=True)
        with self.assertRaises(p.Stop):
            r.dispatch(dict(operation='begin', run=RUN), io.BytesIO())
        self.remote.unlink()
        self.remote.mkdir(mode=0o755)
        self.remote.chmod(0o755)
        with self.assertRaises(p.Stop):
            r.dispatch(dict(operation='begin', run=RUN), io.BytesIO())
    def test_remote_chunk_symlink_not_followed(self):
        with small_geometry():
            r.dispatch(dict(operation='begin', run=RUN), io.BytesIO())
            victim = self.root/'victim'
            victim.write_bytes(b'untouched')
            (self.remote/RUN/'chunk-0000.bin').symlink_to(victim)
            with self.assertRaises(FileExistsError):
                r.dispatch(dict(operation='put', run=RUN, index=0, bytes=1024, sha256='a'*64), io.BytesIO(b'x'*1024))
            self.assertEqual(victim.read_bytes(), b'untouched')
    def test_remote_short_oversized_and_mismatch_never_publish(self):
        with small_geometry():
            for i, data in enumerate((b'x'*1023, b'x'*1025, b'y'*1024)):
                run = '20261106T180000Z-'+('%016x' % i)
                r.dispatch(dict(operation='begin', run=run), io.BytesIO())
                with self.assertRaises(p.Stop):
                    r.dispatch(dict(operation='put', run=run, index=0, bytes=1024, sha256=p.sha(b'x'*1024)), io.BytesIO(data))
                self.assertFalse((self.remote/run/'READY.json').exists())
    def test_remote_reverification_detects_corruption_and_wrong_manifest(self):
        result, _, _ = self.transfer()
        with small_geometry():
            with self.assertRaises(p.Stop):
                r.dispatch(dict(operation='verify', run=RUN, manifest_sha256='0'*64), io.BytesIO())
            f = self.remote/RUN/'system.img'
            with f.open('r+b') as stream:
                stream.seek(19)
                stream.write(b'corrupt')
            with self.assertRaises(p.Stop):
                r.dispatch(dict(operation='verify', run=RUN, manifest_sha256=result['manifest_sha256']), io.BytesIO())
    def test_changed_remote_chunk_blocks_assembly(self):
        class Changed(FilesystemRemote):
            def call(inner, operation, **fields):
                if operation == 'assemble':
                    f = self.remote/RUN/'chunk-0001.bin'
                    f.write_bytes(b'z'*1024)
                return super().call(operation, **fields)
        with small_geometry(), self.assertRaises(p.Stop):
            c.transfer(RUN, self.local, ByteDevice(self.payload), Changed(), self.journal, CODE_HASHES, fixture_input(self.payload))
        self.assertFalse((self.remote/RUN/'READY.json').exists())
        self.assertFalse((self.remote/RUN/'system.img').exists())
    def test_failed_publication_leaves_no_false_host_completion(self):
        with small_geometry(), patch.object(r.os, 'link', side_effect=OSError('publication failed')):
            with self.assertRaises(OSError):
                c.transfer(RUN, self.local, ByteDevice(self.payload), FilesystemRemote(), self.journal, CODE_HASHES, fixture_input(self.payload))
        self.assertFalse((self.local/'COMPLETE.json').exists())
        self.assertFalse((self.remote/RUN/'READY.json').exists())
    def test_host_symlink_collision_no_overwrite(self):
        victim = self.root/'victim'
        victim.write_bytes(b'keep')
        (self.local/'chunk.bin').symlink_to(victim)
        with small_geometry(), self.assertRaises(FileExistsError):
            c.transfer(RUN, self.local, ByteDevice(self.payload), FilesystemRemote(), self.journal, CODE_HASHES, fixture_input(self.payload))
        self.assertEqual(victim.read_bytes(), b'keep')
    def test_host_changed_before_cleanup_is_preserved(self):
        d = ByteDevice(self.payload)
        old = d.clean_chunk
        def mutate():
            old()
            (self.local/'chunk.bin').write_bytes(b'changed')
        d.clean_chunk = mutate
        with small_geometry(), self.assertRaises(p.Stop):
            c.transfer(RUN, self.local, d, FilesystemRemote(), self.journal, CODE_HASHES, fixture_input(self.payload))
        self.assertEqual((self.local/'chunk.bin').read_bytes(), b'changed')
    def test_default_plan_launches_no_subprocess(self):
        with patch.object(c.subprocess, 'run', side_effect=AssertionError('transport forbidden')), \
             patch.object(c.subprocess, 'Popen', side_effect=AssertionError('transport forbidden')), \
             patch('sys.stdout', new_callable=io.StringIO) as out:
            self.assertEqual(c.main([]), 0)
        plan = json.loads(out.getvalue())
        self.assertEqual(plan['mode'], 'PLAN_ONLY')
        self.assertEqual(plan['target']['bytes'], 3753902080)
        self.assertEqual(plan['chunks'], 112)
        self.assertEqual(plan['final_chunk_bytes'], 29360128)
        self.assertEqual(plan['transport'], p.TRANSPORT)
        self.assertEqual(plan['target']['serial'], 'DEVICE_SERIAL_REDACTED')
        self.assertEqual(plan['device_temp_base'], c.BASE+'/'+plan['run'])
    def test_execute_requires_parent_ownership_before_transport(self):
        with patch.object(c.subprocess, 'run', side_effect=AssertionError('transport forbidden')):
            with self.assertRaises(p.Stop):
                c.main(['--execute'])
    def test_no_arbitrary_partition_destination_or_resume_options(self):
        for args in (['--block', '/dev/block/mmcblk0p26'], ['--remote-path', '/tmp/else'], ['--resume'],
                     ['--endpoint', '192.168.68.64:5555'], ['--serial', c.SERIAL], ['--discover']):
            with patch('sys.stderr', new_callable=io.StringIO), self.assertRaises(SystemExit):
                c.main(args)
    def test_manifest_scope_mutations_rejected(self):
        self.transfer()
        m = json.loads((self.local/'manifest.json').read_bytes())
        with small_geometry():
            for mutate in (lambda x: x['target'].update(block='/dev/block/mmcblk0p26'),
                           lambda x: x['target'].update(serial=c.ENDPOINT),
                           lambda x: x['transport'].update(endpoint=c.SERIAL),
                           lambda x: x['transport'].update(endpoint='192.168.68.64:5555'),
                           lambda x: x['transport'].update(secure_adb='0'),
                           lambda x: x.pop('transport'),
                           lambda x: x.update(run='bad'), lambda x: x.update(bytes=3583),
                           lambda x: x.update(assembled_sha256='invalid'),
                           lambda x: x['chunks'][0].update(offset=512),
                           lambda x: x['chunks'][0].update(remote_sha256='0'*64)):
                bad = copy.deepcopy(m)
                mutate(bad)
                with self.assertRaises(p.Stop):
                    p.validate_manifest(bad, RUN)
    def test_ssh_command_quotes_python_and_json_as_arguments(self):
        remote = c.Remote(RUN, self.journal)
        calls = []
        def fake(argv, **kwargs):
            calls.append((argv, kwargs))
            parts = shlex.split(argv[-1])
            self.assertEqual(parts[:2], ['python3', '-c'])
            self.assertEqual(parts[2], remote.code)
            self.assertEqual(json.loads(c.zlib.decompress(c.base64.b64decode(parts[3]))), dict(operation='verify', run=RUN, manifest_sha256='f'*64))
            return subprocess.CompletedProcess(argv, 0, json.dumps(dict(operation='verify', run=RUN)).encode(), b'')
        with patch.object(c.subprocess, 'run', side_effect=fake):
            remote.call('verify', manifest_sha256='f'*64)
        self.assertNotIn('shell', calls[0][1])
        self.assertIn('StrictHostKeyChecking=yes', calls[0][0])
        self.assertEqual(calls[0][1]['stdin'], subprocess.DEVNULL)
    def test_ssh_nonzero_and_lost_ack_stop(self):
        remote = c.Remote(RUN, self.journal)
        with patch.object(c.subprocess, 'run', return_value=subprocess.CompletedProcess([], 255, b'', b'connection lost')):
            with self.assertRaises(p.Stop):
                remote.call('begin')
        with patch.object(c.subprocess, 'run', side_effect=subprocess.TimeoutExpired('fake-ssh', 1)):
            with self.assertRaises(p.Stop):
                remote.call('begin')
    def test_remote_bootstrap_real_local_python(self):
        # Executed locally with verify against a nonexistent fixture path only.
        remote = c.Remote(RUN, self.journal)
        remote.code = remote.code.replace('/srv/android/asus-stock-system-backup', str(self.remote))
        result = subprocess.run([sys.executable, '-c', remote.code,
                                 c.pack_request(dict(operation='verify', run=RUN, manifest_sha256='a'*64))],
                                capture_output=True, timeout=5)
        self.assertEqual(result.returncode, 2)
        self.assertIn(b'FileNotFoundError', result.stderr)
    def test_source_code_pins_actual_files(self):
        values = c.local_inputs()
        self.assertEqual(set(values), set(CODE_HASHES))
        for name, digest in values.items():
            self.assertEqual(hashlib.sha256((SPIKE/'source'/name).read_bytes()).hexdigest(), digest)

    def test_remote_fsync_failure_never_publishes(self):
        with small_geometry():
            r.dispatch(dict(operation='begin', run=RUN), io.BytesIO())
            with patch.object(r.os, 'fsync', side_effect=OSError('disk full or I/O error')):
                with self.assertRaises(OSError):
                    r.dispatch(dict(operation='put', run=RUN, index=0, bytes=1024, sha256=p.sha(b'x'*1024)), io.BytesIO(b'x'*1024))
            self.assertFalse((self.remote/RUN/'READY.json').exists())
    def test_remote_private_files_refuse_hardlink_or_wrong_owner(self):
        with small_geometry():
            r.dispatch(dict(operation='begin', run=RUN), io.BytesIO())
            f = self.remote/RUN/'chunk-0000.bin'
            p.create_file(f, b'x'*1024)
            os.link(f, self.root/'alias')
            with self.assertRaises(p.Stop):
                p.private(f)
            (self.root/'alias').unlink()
            with patch.object(p.os, 'getuid', return_value=os.getuid()+1):
                with self.assertRaises(p.Stop):
                    p.private(f)
    def test_real_geometry_covers_entire_partition_once_per_pass(self):
        rows = p.chunk_layout()
        cursor = 0
        for i, offset, n in rows:
            self.assertEqual(offset, cursor)
            self.assertLessEqual(n, 32*1024*1024)
            self.assertEqual(n % (1024*1024), 0)
            cursor += n
        self.assertEqual(cursor, 3753902080)
        self.assertEqual(len(rows), 112)

    def test_invalid_slices_never_invoke_root(self):
        device = c.Device(RUN, self.journal)
        for args in (('userdata', 0, c.CHUNK), ('a', -c.CHUNK, c.CHUNK),
                     ('a', c.SIZE, c.CHUNK), ('a', 1, c.CHUNK), ('a', 0, c.CHUNK*2)):
            with patch.object(device, 'root') as root, self.assertRaises(p.Stop):
                device.stage(*args)
            root.assert_not_called()


class HealthTests(unittest.TestCase):
    setUp = BackupTests.setUp
    tearDown = BackupTests.tearDown

    def snapshot(self, script, overrides=None):
        nonce = re.search(r'BEGIN_([0-9a-f]{32})', script).group(1)
        values = dict(health.PROPS, selinux='Enforcing')
        values.update(overrides or {})
        return '\n'.join(['BEGIN_'+nonce]+[k+'='+v for k,v in values.items()]+['END_'+nonce])+'\n'

    def fake(self, overrides=None, root_fault=None):
        def run(argv, input=None, **kwargs):
            if argv == c.ADB+['get-serialno']:
                out = (overrides or {}).get('endpoint', c.ENDPOINT)
            elif argv[:5] == c.ADB+['shell', '-T']:
                out = self.snapshot(argv[-1], {k:v for k,v in (overrides or {}).items() if k != 'endpoint'})
            elif argv == [sys.executable, str(c.HELPER)]:
                token = re.search(r'ASUS_SYSTEM_RC_([0-9a-f]{32})=', input).group(1)
                out = f'ASUS_SYSTEM_RC_{token}={23 if root_fault == "inner" else 0}\n'
                if root_fault == 'lost':
                    out = ''
                return subprocess.CompletedProcess(argv, 255 if root_fault == 'dispatch' else 0, out, '')
            else:
                self.assertEqual(argv[:4], c.ADB+['shell'])
                self.assertIn(c.PARENT_PATH_GUARD, argv[-1])
                out = ''
            return subprocess.CompletedProcess(argv, 0, out, '')
        return run

    def test_batched_identity_and_distinct_endpoint(self):
        with patch.object(c.subprocess, 'run', side_effect=self.fake()) as runner:
            c.Device(RUN, self.journal).healthy()
        self.assertEqual(runner.call_count, 2)
        self.assertNotEqual(c.SERIAL, c.ENDPOINT)

    def test_wrong_identity_endpoint_secure_adb_or_enforcing_never_retried(self):
        cases = [{k:'WRONG'} for k in health.PROPS] + [{'endpoint':c.SERIAL}, {'selinux':'Permissive'}]
        for changes in cases:
            with patch.object(c.subprocess, 'run', side_effect=self.fake(changes)) as runner, self.assertRaises(p.Stop):
                c.Device(RUN, self.journal).preflight()
            self.assertLessEqual(runner.call_count, 2)

    def test_readonly_health_255_and_timeout_retry_bound_with_receipts(self):
        for failure in (subprocess.CompletedProcess([], 255, '', 'lost'), subprocess.TimeoutExpired('mock', 12)):
            logs = []
            effects = [failure, failure, subprocess.CompletedProcess([], 0, 'ok', '')]
            with patch.object(health.subprocess, 'run', side_effect=effects) as runner:
                result = health.query(c.ADB+['get-serialno'], lambda kind, **fields: logs.append((kind, fields)))
            self.assertEqual(result, 'ok')
            self.assertEqual(runner.call_count, 3)
            self.assertEqual(len(logs), 6)
            with patch.object(health.subprocess, 'run', side_effect=[failure]*3) as runner, self.assertRaises(p.Stop):
                health.query(c.ADB+['get-serialno'], self.journal.event)
            self.assertEqual(runner.call_count, 3)

    def test_partial_failed_health_response_is_not_retried(self):
        failures = [subprocess.CompletedProcess([],255,'OTHER_DEVICE','lost'),
                    subprocess.TimeoutExpired('mock',12,output=b'partial identity')]
        for failure in failures:
            with patch.object(health.subprocess,'run',side_effect=[failure]) as runner,self.assertRaises(p.Stop):
                health.query(c.ADB+['get-serialno'],self.journal.event)
            self.assertEqual(runner.call_count,1)

    def test_error_status_is_not_retryable(self):
        with patch.object(health.subprocess, 'run', return_value=subprocess.CompletedProcess([], 1, '', 'error')) as runner, self.assertRaises(p.Stop):
            health.healthy(self.journal.event)
        self.assertEqual(runner.call_count, 1)

    def test_strict_snapshot_nonce_duplicates_trailing_lines(self):
        nonce='f'*32
        good=self.snapshot(health.snapshot_script(nonce))
        health.parse_snapshot(good,nonce)
        for text in (good+'extra\n', good.replace('END_'+nonce, 'END_'+'e'*32), good+good, good.replace('selinux=Enforcing', 'selinux=Permissive')):
            with self.assertRaises(p.Stop): health.parse_snapshot(text,nonce)

    def test_root_uncertainty_and_inner_failure_never_retry(self):
        for fault in ('inner', 'lost', 'dispatch'):
            with patch.object(c.subprocess, 'run', side_effect=self.fake(root_fault=fault)) as runner, self.assertRaises(p.Stop):
                c.Device(RUN, self.journal).preflight()
            self.assertEqual(sum(call.args[0] == [sys.executable, str(c.HELPER)] for call in runner.call_args_list),1)

    def test_security_change_after_root_stops(self):
        base=self.fake()
        dispatched=[]
        def changed(argv, **kw):
            if argv == [sys.executable,str(c.HELPER)]: dispatched.append(True)
            if dispatched and argv[:5] == c.ADB+['shell','-T']:
                return subprocess.CompletedProcess(argv,0,self.snapshot(argv[-1],{'ro.adb.secure':'0'}),'')
            return base(argv,**kw)
        with patch.object(c.subprocess,'run',side_effect=changed),self.assertRaises(p.Stop):
            c.Device(RUN,self.journal).preflight()
        self.assertEqual(len(dispatched),1)

    def test_dependencies_and_fixed_ssh_scope(self):
        c.local_inputs()
        self.assertEqual(c.HELPER,SPIKE/'scripts/root_shell_batched.py')
        self.assertEqual(c.ROOT_BINARY_HASH,'328632e853ff6427af9f35cb83a91d9e960f35d01188ee66d46ae9c7ce7c7827')
        self.assertEqual(c.SSH[-1],'android@IP_REDACTED')
        self.assertIn('HostKeyAlias=compute.8549823276971553556',c.SSH)
        for dependency in ('HELPER','ROOT_BINARY'):
            bad=self.root/dependency
            for kind in ('missing','changed','symlink'):
                if kind == 'changed': bad.write_bytes(b'bad')
                if kind == 'symlink':
                    bad.unlink();bad.symlink_to(getattr(c,dependency))
                with patch.object(c,dependency,bad), patch.object(c.subprocess,'run',side_effect=AssertionError('transport forbidden')),self.assertRaises(p.Stop):
                    c.Device(RUN,self.journal).preflight()

    def test_action_without_execute_is_offline(self):
        for args in (['preflight'],['backup','--exclusive-device-owner'],['verify','--run-id',RUN,'--manifest-sha256','a'*64]):
            with patch.object(c.subprocess,'run',side_effect=AssertionError('transport forbidden')),patch('sys.stdout',new_callable=io.StringIO) as out:
                self.assertEqual(c.main(args),0)
            self.assertEqual(json.loads(out.getvalue())['mode'],'PLAN_ONLY')


class StreamTests(unittest.TestCase):
    def test_device_binary_requires_shell_v2_without_pty_or_silent_fallback(self):
        journal = type('J', (), {'event': lambda *a, **k: None})()
        device = c.Device(RUN, journal)
        device.inodes = {'a': 123}
        device.size = 5
        received = bytearray()
        def transport(argv, length, consume):
            self.assertEqual(argv[:5], ['adb', '-s', 'IP_REDACTED:5555', 'shell', '-T'])
            self.assertIn('cat '+c.BASE+'/'+RUN+'/a.bin', argv[5])
            self.assertNotIn('asus-stock-system-stream-backup', argv[5])
            self.assertIn("[ ! -L /data/local/tmp ]", argv[5])
            self.assertIn("%i", argv[5])
            self.assertEqual(length, 5)
            consume(bytes([0, 13, 10, 255, 128]))
            return 5
        good = subprocess.CompletedProcess([], 0, 'cmd\nshell_v2\n', '')
        with patch.object(device, 'command', return_value=good), patch.object(c, 'stream_process', side_effect=transport):
            device.binary('a', 5, received.extend)
        self.assertEqual(received, bytes([0, 13, 10, 255, 128]))
        unsupported = subprocess.CompletedProcess([], 0, 'cmd\n', '')
        with patch.object(device, 'command', return_value=unsupported), patch.object(c, 'stream_process') as stream:
            with self.assertRaises(p.Stop):
                device.binary('a', 5, received.extend)
            stream.assert_not_called()

    def test_binary_preservation_real_subprocess(self):
        data = bytes(range(256))*256+b'\x00\r\n\xff\x80'
        result = bytearray()
        n = c.stream_process([sys.executable, '-c', 'import sys;sys.stdout.buffer.write(bytes(range(256))*256+bytes([0,13,10,255,128]))'], len(data), result.extend)
        self.assertEqual(n, len(data))
        self.assertEqual(result, data)
    def test_short_oversized_nonzero_timeout(self):
        for script, length, timeout in [('import sys;sys.stdout.buffer.write(b"x"*3)', 4, 5),
                                        ('import sys;sys.stdout.buffer.write(b"x"*5)', 4, 5),
                                        ('import sys;sys.stdout.buffer.write(b"x"*4);sys.exit(7)', 4, 5),
                                        ('import time;time.sleep(1)', 4, 0.05)]:
            with self.subTest(script=script), self.assertRaises(p.Stop):
                c.stream_process([sys.executable, '-c', script], length, lambda b: None, timeout=timeout)
    def test_32mib_stream_memory_and_disk_bound(self):
        with tempfile.TemporaryDirectory(dir=SPIKE/'tests') as temp:
            path = Path(temp)/'chunk.bin'
            size, max_buffer = 32*1024*1024, 0
            h = hashlib.sha256()
            with path.open('wb') as f:
                def consume(b):
                    nonlocal max_buffer
                    max_buffer = max(max_buffer, len(b))
                    f.write(b)
                    h.update(b)
                tracemalloc.start()
                c.stream_process([sys.executable, '-c', 'import sys\nfor i in range(32): sys.stdout.buffer.write(bytes(range(256))*4096)'], size, consume)
                _, peak = tracemalloc.get_traced_memory()
                tracemalloc.stop()
            self.assertEqual(path.stat().st_size, size)
            self.assertLessEqual(max_buffer, 1024*1024)
            self.assertLess(peak, 8*1024*1024)
            self.assertEqual(p.digest_file(path), (size, h.hexdigest()))
            OBSERVATIONS.append(dict(case='real_local_32MiB_binary_stream', bytes=size, max_callback_bytes=max_buffer,
                                     python_tracemalloc_peak_bytes=peak, local_payload_files=1))


class ShellGuardTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='shell-', dir=SPIKE/'tests')
        self.root = Path(self.tmp.name).resolve()
    def tearDown(self):
        self.tmp.cleanup()
    def guard(self, changes=None):
        changes = changes or {}
        props = dict(c.PROPS)
        props.update(changes.get('props', {}))
        sysfs = {'/sys/class/block/mmcblk0p25/partition': '25', '/sys/class/block/mmcblk0p25/start': '1072424',
                 '/sys/class/block/mmcblk0p25/size': '7331840', '/sys/class/block/mmcblk0p25/dev': '179:25',
                 '/sys/class/block/mmcblk0/queue/logical_block_size': '512'}
        sysfs.update(changes.get('sysfs', {}))
        mounts = changes.get('mounts', c.BLOCK+' /system ext4 ro,seclabel,relatime 0 0\n')
        info = changes.get('info', '21 0 179:25 / /system ro,relatime - ext4 '+c.BLOCK+' ro,seclabel\n')
        (self.root/'mounts').write_text(mounts)
        (self.root/'mountinfo').write_text(info)
        def shell_function(name, values, default='exit 99'):
            return name+'() { case "$1" in\n'+''.join(shlex.quote(k)+') printf \'%s\\n\' '+shlex.quote(v)+' ;;\n' for k,v in values.items())+'*) '+default+' ;; esac; }\n'
        script = 'set -eu\nid() { printf "0\\n"; }\n'
        script += shell_function('getprop', props)
        script += shell_function('cat', sysfs)
        script += 'readlink() { if [ "$2" = /data/local/tmp ]; then printf \'%s\\n\' '+shlex.quote(changes.get('tmp_alias', '/data/local/tmp'))+'; else printf \'%s\\n\' '+shlex.quote(changes.get('alias', c.BLOCK))+'; fi; }\n'
        listing = changes.get('listing', 'brw-r----- 1 0 1000 179, 25 2026-11-06 15:29 '+c.BLOCK)
        script += 'ls() { printf \'%s\\n\' '+shlex.quote(listing)+'; }\n'
        guard = c.DEVICE_GUARD.replace('[ -b '+c.BLOCK+' ]', '[ '+shlex.quote(changes.get('block', 'yes'))+' = yes ]')
        guard = guard.replace('/proc/self/mountinfo', str(self.root/'mountinfo')).replace('/proc/mounts', str(self.root/'mounts'))
        script += guard+'\nprintf GUARD_PASSED\n'
        return subprocess.run(['/bin/sh'], input=script, text=True, capture_output=True, timeout=5)
    def test_valid_device_fixture_passes_actual_shell_guard(self):
        result = self.guard()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('GUARD_PASSED', result.stdout)
    def test_root_canonical_parent_still_required(self):
        self.assertNotEqual(self.guard({'tmp_alias': '/different/path'}).returncode, 0)
    def test_unprivileged_parent_checks_without_canonical_directory_access(self):
        data = self.root/'data'
        local = data/'local'
        temporary = local/'tmp'
        temporary.mkdir(parents=True)
        values = {str(data): '1000:1000:771', str(local): '0:0:751', str(temporary): '2000:2000:771'}
        def execute(owners):
            # Android's shell can stat known paths but cannot enumerate /data
            # for readlink -f. Keep that failure in the fixture.
            script = 'set -eu\nreadlink() { exit 99; }\nstat() { case "$3" in\n'
            script += ''.join(shlex.quote(k)+') printf \'%s\\n\' '+shlex.quote(v)+' ;;\n' for k,v in owners.items())
            script += '*) exit 98 ;; esac; }\n'
            script += c.PARENT_PATH_GUARD.replace('/data', str(data))+'\nprintf PARENT_PASSED\n'
            return subprocess.run(['/bin/sh'], input=script, text=True, capture_output=True, timeout=5)
        self.assertEqual(execute(values).returncode, 0)
        for path in values:
            wrong = dict(values)
            wrong[path] = '999:999:777'
            self.assertNotEqual(execute(wrong).returncode, 0)
        temporary.rmdir()
        other = self.root/'other'
        other.mkdir()
        temporary.symlink_to(other, target_is_directory=True)
        self.assertNotEqual(execute(values).returncode, 0)
    def test_identity_mismatch_each_field(self):
        for key in c.PROPS:
            with self.subTest(key=key):
                result = self.guard({'props': {key: 'WRONG'}})
                self.assertNotEqual(result.returncode, 0)
                self.assertNotIn('GUARD_PASSED', result.stdout)
    def test_geometry_mismatch_each_field(self):
        for path in ('mmcblk0p25/partition', 'mmcblk0p25/start', 'mmcblk0p25/size', 'mmcblk0p25/dev',
                     'mmcblk0/queue/logical_block_size'):
            with self.subTest(path=path):
                self.assertNotEqual(self.guard({'sysfs': {'/sys/class/block/'+path: '999'}}).returncode, 0)
        self.assertNotEqual(self.guard({'alias': '/dev/block/mmcblk0p26'}).returncode, 0)
        self.assertNotEqual(self.guard({'block': 'no'}).returncode, 0)
    def test_device_number_ls_not_android_unsupported_stat(self):
        good = 'brw-r----- 1 0 1000 179, 25 2026-11-06 15:29 '+c.BLOCK
        for wrong in ('', good.replace('179,', '180,'), good.replace(' 25 ', ' 26 '), good.replace(c.BLOCK, '/dev/block/mmcblk0p26')):
            self.assertNotEqual(self.guard({'listing': wrong}).returncode, 0)
        self.assertNotIn('%t', c.DEVICE_GUARD)
        self.assertNotIn('%T', c.DEVICE_GUARD)
    def test_writable_missing_duplicate_or_wrong_system_mount(self):
        good = c.BLOCK+' /system ext4 ro,seclabel 0 0\n'
        for mounts in (good.replace('ro,', 'rw,'), '', good*2, good.replace('ext4', 'f2fs')):
            self.assertNotEqual(self.guard({'mounts': mounts}).returncode, 0)
        info = '21 0 179:25 / /system ro,relatime - ext4 '+c.BLOCK+' ro,seclabel\n'
        for wrong in (info.replace(' /system ro,', ' /system rw,'), '',
                      info+'22 0 179:25 / /other rw,relatime - ext4 '+c.BLOCK+' rw\n'):
            self.assertNotEqual(self.guard({'info': wrong}).returncode, 0)
    def test_nonce_status_survives_outer_success_trap(self):
        token = 'a'*32
        body = '(exit 23)\nprintf SHOULD_NOT_RUN'
        script = "trap 'true' EXIT\n"+c.root_envelope(body, token).replace(c.DEVICE_GUARD, ':')
        result = subprocess.run(['/bin/sh'], input=script, text=True, capture_output=True, timeout=5)
        self.assertEqual(result.returncode, 0)
        self.assertNotIn('SHOULD_NOT_RUN', result.stdout)
        with self.assertRaisesRegex(p.Stop, 'status 23'):
            c.root_status(result, token)
    def test_missing_duplicate_status_or_helper_error_refused(self):
        token = 'a'*32
        for rc, out in ((0, ''), (0, f'ASUS_SYSTEM_RC_{token}=0\n'*2), (1, f'ASUS_SYSTEM_RC_{token}=0\n'),
                        (0, 'ASUS_SYSTEM_RC_'+'b'*32+'=0\n')):
            with self.assertRaises(p.Stop):
                c.root_status(subprocess.CompletedProcess([], rc, out, ''), token)
    def test_device_staging_symlink_and_alien_owner(self):
        real = self.root/'real'
        real.mkdir(mode=0o700)
        stage = self.root/'stage'
        stage.symlink_to(real, target_is_directory=True)
        guard = c.directory_guard().replace(c.BASE, str(stage))
        self.assertNotEqual(subprocess.run(['/bin/sh'], input='set -eu\n'+guard, text=True, capture_output=True).returncode, 0)
        stage.unlink()
        stage.mkdir(mode=0o700)
        guard = c.directory_guard().replace(c.BASE, str(stage))
        for owner in ('0:0:700', '2000:2000:777'):
            script = 'set -eu\nreadlink() { printf \'%s\' '+shlex.quote(str(stage))+'; }\nstat() { printf \'%s\' '+shlex.quote(owner)+'; }\n'+guard
            self.assertNotEqual(subprocess.run(['/bin/sh'], input=script, text=True, capture_output=True).returncode, 0)
    def test_generated_root_scripts_syntax_and_fixed_read_only_scope(self):
        scripts = []
        d = c.Device(RUN, object())
        def root(body):
            scripts.append(c.root_envelope(body, 'c'*32))
            return 'ASUS_STAGE_INODE=12345\n'
        d.root = root
        d.journal = type('J', (), {'event': lambda *a, **k: None})()
        d.preflight()
        d.setup()
        d.stage('a', 0, c.CHUNK)
        d.stage('b', 0, c.CHUNK)
        d.clean_chunk()
        d.finish()
        reads = []
        for script in scripts:
            result = subprocess.run(['/bin/sh', '-n'], input=script, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertNotRegex(script, r'\b(reboot|fastboot|mount|umount|flash_image|sha256sum)\b')
            self.assertNotIn('conv=', script)
            self.assertNotIn('head -c', script)
            for src, dest, bs, skip, count in re.findall(r'dd if=(\S+) of=(\S+) bs=(\d+) skip=(\d+) count=(\d+)', script):
                self.assertEqual(src, c.BLOCK)
                self.assertIn(dest, [c.BASE+'/'+RUN+'/a.bin', c.BASE+'/'+RUN+'/b.bin'])
                self.assertEqual(int(bs)*int(count), c.CHUNK)
                self.assertEqual(script.count(c.DEVICE_GUARD), 2)
                reads.append(dest)
            self.assertNotRegex(script, r'\bof=/dev/')
            self.assertNotIn('rm -r', script)
        self.assertEqual(len(reads), 2)
    def test_preflight_df_parsing_without_pipeline(self):
        bodies = []
        d = c.Device(RUN, None)
        d.root = bodies.append
        d.preflight()
        body = bodies[0]
        body = body[body.index('data_free='):]
        for free, success in ((3810960, True), (131071, False)):
            df = 'Filesystem 1K-blocks Used Available Use% Mounted on\n/dev/block/dm-0 12000000 8000000 '+str(free)+' 80% /data\n'
            script = "set -eu\ndf() { printf '%s' "+shlex.quote(df)+'; }\n'+body
            result = subprocess.run(['/bin/sh'], input=script, text=True, capture_output=True)
            self.assertEqual(result.returncode == 0, success, result.stderr)


if __name__ == '__main__':
    def offline_only(event, args):
        if event == 'subprocess.Popen':
            executable, argv = args[:2]
            allowed = (executable == sys.executable and argv[:2] == [sys.executable, '-c']) or (
                executable == '/bin/sh' and argv in (['/bin/sh'], ['/bin/sh', '-n']))
            if not allowed:
                raise AssertionError('Offline tests forbid external transport/helper execution')
        if event in ('socket.connect', 'socket.getaddrinfo'):
            raise AssertionError('Offline tests forbid endpoint probing')
    sys.addaudithook(offline_only)
    os.umask(0o077)
    output = io.StringIO()
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    import continuation_cases
    continuation_cases.base = sys.modules[__name__]
    suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(continuation_cases))
    result = unittest.TextTestRunner(stream=output, verbosity=2).run(suite)
    (SPIKE/'evidence/offline-tests.txt').write_text(output.getvalue())
    (SPIKE/'evidence/offline-tests.json').write_text(json.dumps(dict(
        tests_run=result.testsRun, failures=len(result.failures), errors=len(result.errors),
        device_contacted=False, ssh_contacted=False, vm_contacted=False,
        transport='IP_REDACTED:5555 (mocked only)', hardware_serial=c.SERIAL,
        external_transport_blocked_by_audit_hook=True,
        boundaries='fake byte source; real local remote-worker filesystem; mocked subprocess SSH; real local binary and shell fixtures',
        observations=OBSERVATIONS), indent=2)+'\n')
    print(output.getvalue(), end='')
    raise SystemExit(0 if result.wasSuccessful() else 1)
