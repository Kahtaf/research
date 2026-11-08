"""Fixed read-only rescue USB measurement. CLI is always PLAN_ONLY.

Parent API only: observe(Commissioning(...), live_install_completion_token, ...).
Commissioning is external parent evidence, not physical proof produced here.
"""
import argparse
import builtins
import dataclasses
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import re
import selectors
import socket
import stat
import subprocess
import time
import types
import uuid

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
BUILD = WORKSPACE / '2026-11-06-asus-stock-only-ram-rescue-build'
DEPLOY = WORKSPACE / '2026-11-06-asus-rescue-pin-monotonic-fix'
MEASURE = WORKSPACE / '2026-11-06-asus-readonly-rescue-timing/source/measure.py'
MEASURE_SHA = '759cf4eab6d2a2c3c101eadabedfe19bcd5050d0e071d5b0d15c54f5f9055803'
DEPLOY_SHA = '24196e415ac61a56fac5ef1ce145181c90915323129600cc16d67096d1afc62e'
MANIFEST = '605cdec038dafe3dddabfe92b8bd6cd189734f740230dfc362d02a43421e4e47'
P10 = '3f99c785cca60bf56c2505711e2d26b72623daf28180515d44c5ba2abf03a44a'
IMAGE = '5a61d3d65a7ba6b29745a965d9911ab4483c951a0327339839a0541bcb9ab30f'
ADB = Path('/opt/homebrew/Caskroom/android-platform-tools/37.0.1/platform-tools/adb')
ADB_SHA = '1811e253b21b12cbfda7201ebaf86c10e7ddcb5c606a7a81f7c82b4c429c2d3b'
LOCK = WORKSPACE / '2026-11-06-asus-recovery-control-transport/evidence/execute.lock'
RUNS = ROOT / 'evidence/runs'
DEPLOY_FILES = {
 'profile.json': '661d93cbc012d839429bb1b87431fb83b5f646833ee59d307e0e60461b7cda6f',
 'source/adapter.py': '81555d5b4374e4faca65e98f2212003bada3afba37ee906dd3b72a9fcfe23c01',
 'source/engine.py': '630c4aaadbb418dc0af1f5a00628b3ec16117bb165707b4d18794c124464a681',
 'source/root_dispatch.py': '38c8030193f32084b6549bf81f6e1d2f9428fb516a6853295eb1adb4208407bc',
 'source/preserved.json': '80475bab124d355255ce10d4224ffc89ac20b61ddc440d88303f5fa47638ba8c',
}
INPUTS = {
 'artifacts/candidate/UNAPPROVED-STOCK-ONLY.img': IMAGE,
 'artifacts/original-stock.manifest': MANIFEST,
 'source/rescue.c': '23b0af1a8c813ae925459bf4614f768a5f90e5a76efb49bf8523135159c72c49',
 'source/common.h': '90fe60e79b3cc3932dab7e824bc803bb18ba086ea079beca8298c34ccf2a53c3',
}
IDENTITY = dict(serial='DEVICE_SERIAL_REDACTED', state='device', product='p00a_target_rescue',
                model='P00A_target_rescue', device='p00a')
STDERR_LIMIT = 8192
OUTPUT_LIMIT = 65536


class Refused(ValueError):
    pass


def require(ok, message):
    if not ok:
        raise Refused(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path, maximum=20_000_000):
    path = Path(path).absolute()
    require(not any(p.is_symlink() for p in (path, *path.parents)), 'Symlink input')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        require(stat.S_ISREG(os.fstat(stream.fileno()).st_mode), 'Regular input required')
        data = stream.read(maximum + 1)
    require(len(data) <= maximum, 'Oversized input')
    return data


def object_sha(obj):
    return sha(json.dumps(obj, sort_keys=True, separators=(',', ':'), allow_nan=False).encode())


def module_bytes(name, path, data, imports=None):
    mod = types.ModuleType(name)
    mod.__file__ = str(path)
    if imports:
        original = builtins.__import__
        def isolated(name, *args, **kwargs):
            return imports[name] if name in imports else original(name, *args, **kwargs)
        mod.__dict__['__builtins__'] = dict(vars(builtins), __import__=isolated)
    exec(compile(data, str(path), 'exec'), mod.__dict__)
    return mod


def check_sources():
    data = read(MEASURE)
    require(sha(data) == MEASURE_SHA, 'Measurement source drift')
    for name, pin in INPUTS.items():
        require(sha(read(BUILD / name)) == pin, 'Manifest/candidate/target source drift')
    files = {name: read(DEPLOY / name) for name in DEPLOY_FILES}
    require({name: sha(data) for name, data in files.items()} == DEPLOY_FILES, 'Deployment source drift')
    require(object_sha(DEPLOY_FILES) == DEPLOY_SHA, 'Deployment code receipt drift')
    return data, files


def load_reviewed():
    """No parent_client import, CLI, armed contract, root helper or dispatch invocation."""
    data, files = check_sources()
    # Pin before compile; root_dispatch is isolated, without sys.path/sys.modules mutation.
    root = module_bytes('readonly_root_dependency', DEPLOY / 'source/root_dispatch.py', files['source/root_dispatch.py'])
    deploy = module_bytes('readonly_install_verifier', DEPLOY / 'source/adapter.py', files['source/adapter.py'],
                          {'root_dispatch': root})
    measure = module_bytes('reviewed_measure', MEASURE, data)
    return measure, deploy


@dataclasses.dataclass(frozen=True)
class Commissioning:
    # Made in memory by the parent after its independent physical commissioning.
    run_id: str
    rescue_session_id: str
    commissioning_reference: str
    commissioning_sha256: str
    install_state_sha256: str
    usb_topology: str
    transport_id: int
    created_wall: float
    created_monotonic: float
    host_clock_epoch: str
    image_sha256: str = IMAGE
    full_p10_sha256: str = P10
    manifest_sha256: str = MANIFEST
    usb_vid: str = '0e8d'
    usb_pid: str = '201c'


def canonical(value):
    require(type(value) is str and str(uuid.UUID(value)) == value, 'Canonical UUID required')
    return value


def check_binding(binding, epoch):
    require(type(binding) is Commissioning, 'Parent in-memory commissioning required')
    canonical(binding.run_id)
    canonical(binding.rescue_session_id)
    require(binding.image_sha256 == IMAGE and binding.full_p10_sha256 == P10 and
            binding.manifest_sha256 == MANIFEST, 'Commissioning image/manifest drift')
    require(binding.usb_vid == '0e8d' and binding.usb_pid == '201c', 'Wrong rescue USB descriptors')
    require(type(binding.transport_id) is int and 0 < binding.transport_id <= 2**63-1,
            'Positive explicit transport ID required')
    require(re.fullmatch('[0-9A-Za-z.:_-]{1,128}', binding.usb_topology or ''), 'USB topology required')
    require(type(binding.commissioning_reference) is str and
            0 < len(binding.commissioning_reference) <= 1024, 'Parent commissioning reference required')
    for value in (binding.commissioning_sha256, binding.install_state_sha256):
        require(type(value) is str and re.fullmatch('[0-9a-f]{64}', value), 'Evidence digest required')
    require(binding.host_clock_epoch == epoch, 'Other host boot epoch')
    for now, before in ((time.time(), binding.created_wall), (time.monotonic(), binding.created_monotonic)):
        require(type(before) in (int, float) and math.isfinite(before) and 0 <= now-before <= 180,
                'Stale/future rescue operational binding')


def select_usb(raw, binding):
    text = raw.decode('ascii')
    lines = text.splitlines()
    require(lines and lines[0] == 'List of devices attached', 'Invalid USB enumeration')
    rows = []
    for line in lines[1:]:
        if not line.strip():
            continue
        words = line.split()
        require(len(words) >= 2, 'Malformed USB row')
        row = dict(serial=words[0], state=words[1])
        for word in words[2:]:
            key, sep, value = word.partition(':')
            require(sep and value and key not in row, 'Duplicate/malformed USB field')
            row[key] = value
        rows.append(row)
    require(len({r['serial'] for r in rows}) == len(rows), 'Duplicate serial')
    require(all(re.fullmatch('[1-9][0-9]*', r.get('transport_id', '')) for r in rows), 'Invalid transport ID')
    require(len({r['transport_id'] for r in rows}) == len(rows), 'Duplicate transport ID')
    candidates = [r for r in rows if 'usb' in r or r['serial'] == IDENTITY['serial']]
    require(len(candidates) == 1, 'Ambiguous/missing physical USB selection')
    row = candidates[0]
    require(all(row.get(k) == v for k, v in IDENTITY.items()), 'Wrong rescue USB identity/state')
    require(row.get('usb') == binding.usb_topology and
            row.get('transport_id') == str(binding.transport_id), 'USB topology/transport changed')
    return row


class PipeStream:
    """One non-PTY child, raw stdout, nonblocking stdin and bounded stderr retention."""
    def __init__(self, argv, deadline, *, before_send=lambda: None):
        self.deadline = deadline
        self.timeout_at = deadline
        self.before_send = before_send
        self.sent = False
        self.closed = False
        self.stderr_bytes = 0
        # Retain no stderr contents: even a malicious endpoint echoing the token cannot persist it.
        self.stderr_retained = b''
        self.sel = selectors.DefaultSelector()
        try:
            self.proc = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE, bufsize=0, close_fds=True,
                                         env={'PATH': '/usr/bin:/bin', 'HOME': os.environ.get('HOME', '/')})
        except BaseException:
            self.sel.close()
            raise
        try:
            for stream in (self.proc.stdin, self.proc.stdout, self.proc.stderr):
                os.set_blocking(stream.fileno(), False)
            self.sel.register(self.proc.stdout, selectors.EVENT_READ, 'stdout')
            self.sel.register(self.proc.stderr, selectors.EVENT_READ, 'stderr')
        except BaseException:
            self.dispose()
            raise

    def settimeout(self, seconds):
        require(math.isfinite(seconds) and seconds > 0, 'Invalid stream timeout')
        self.timeout_at = min(self.deadline, time.monotonic() + seconds)

    def _events(self):
        left = min(self.deadline, self.timeout_at) - time.monotonic()
        if left <= 0:
            raise TimeoutError('Whole host deadline')
        events = self.sel.select(left)
        if not events:
            raise TimeoutError('Whole host deadline')
        return events

    def _stderr(self, key):
        data = os.read(key.fd, STDERR_LIMIT)
        self.stderr_bytes = min(2**63-1, self.stderr_bytes + len(data))
        if not data:
            self.sel.unregister(key.fileobj)

    def sendall(self, data):
        require(not self.sent, 'Only one request allowed')
        self.sent = True
        self.before_send()
        self.sel.register(self.proc.stdin, selectors.EVENT_WRITE, 'stdin')
        view = memoryview(data)
        try:
            while view:
                for key, _ in self._events():
                    if key.data == 'stderr':
                        self._stderr(key)
                    elif key.data == 'stdin':
                        try:
                            n = os.write(key.fd, view[:65536])
                            view = view[n:]
                        except BlockingIOError:
                            pass
                    elif key.data == 'stdout':
                        # No response can legitimately precede the whole fixed request.
                        raise Refused('Premature child output during send')
        finally:
            self.sel.unregister(self.proc.stdin)

    def recv(self, count):
        while True:
            for key, _ in self._events():
                if key.data == 'stderr':
                    self._stderr(key)
                elif key.data == 'stdout':
                    return os.read(key.fd, count)

    def close(self):
        # measure() closes its stream before the caller checks shell_v2 completion.
        if not self.closed:
            self.closed = True
            self.proc.stdin.close()

    def finish(self, maximum=0):
        """Require stdout/stderr EOF AND the child's genuine remote exit result."""
        self.close()
        self.timeout_at = self.deadline
        output = bytearray()
        while self.sel.get_map():
            for key, _ in self._events():
                if key.data == 'stderr':
                    self._stderr(key)
                else:
                    data = os.read(key.fd, 8192)
                    if not data:
                        self.sel.unregister(key.fileobj)
                    else:
                        output.extend(data)
                        require(len(output) <= maximum, 'Unexpected/excess child stdout')
        left = self.deadline - time.monotonic()
        if left <= 0:
            raise TimeoutError('Remote exit deadline')
        rc = self.proc.wait(timeout=left)
        require(rc == 0, 'Child/remote shell completion failed')
        return bytes(output)

    def dispose(self):
        self.close()
        if self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=0.25)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait(timeout=1)
        self.sel.close()
        self.proc.stdout.close()
        self.proc.stderr.close()


def query(argv, deadline):
    child = PipeStream(argv, min(deadline, time.monotonic()+12))
    try:
        return child.finish(OUTPUT_LIMIT)
    finally:
        child.dispose()


def server_version(deadline):
    """Fixed, read-only host:version probe; never bootstrap a missing/mismatched server.

    Protocol 0x29 is the constant in this hash-pinned CLI. This is host loopback,
    not a target shell query. The parent owns server lifetime under the shared lock.
    """
    end = min(deadline, time.monotonic() + 2)
    left = end - time.monotonic()
    require(left > 0, 'Server probe deadline')
    with socket.create_connection(('127.0.0.1', 5037), timeout=left) as stream:
        stream.settimeout(max(0.000001, end - time.monotonic()))
        stream.sendall(b'000chost:version')
        data = bytearray()
        while True:
            left = end - time.monotonic()
            if left <= 0:
                raise TimeoutError('Server version deadline')
            stream.settimeout(left)
            part = stream.recv(13-len(data))
            if not part:
                break
            data.extend(part)
            require(len(data) <= 12, 'Unexpected server version framing')
        require(data == b'OKAY00040029', 'Missing/mismatched existing ADB server; stop')


def durable(log, value):
    log.write(json.dumps(value, sort_keys=True, allow_nan=False) + '\n')
    log.flush()
    os.fsync(log.fileno())


def sync_directory(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def verify_self(expected):
    require(expected == LOADED_SOURCE_SHA and sha(read(Path(__file__))) == expected,
            'Host transport source drift/unreviewed code')


def accept_completion(binding, *, exit_status, stdout, expected_source_sha256):
    """Offline parent acceptance: lost status/stdout never reconstructed from a file."""
    verify_self(expected_source_sha256)
    require(type(exit_status) is int and exit_status == 0, 'UNKNOWN invocation completion')
    require(type(stdout) is bytes and 0 < len(stdout) <= 16384, 'UNKNOWN result stdout')
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, 'Duplicate result key')
            result[key] = value
        return result
    def decode(raw):
        return json.loads(raw, object_pairs_hook=unique,
                          parse_constant=lambda value: (_ for _ in ()).throw(Refused('Nonfinite result')))
    result = decode(stdout)
    directory = RUNS / canonical(binding.rescue_session_id)
    raw = read(directory / 'events.jsonl', 65536)
    require(raw.endswith(b'\n'), 'Incomplete terminal evidence')
    rows = [decode(row) for row in raw.splitlines()]
    require(len(rows) == 2 and rows[0].get('result') == 'UNKNOWN' and rows[-1] == result,
            'UNKNOWN terminal evidence')
    require(rows[0].get('session') == dataclasses.asdict(binding) and
            rows[0].get('source_sha256') == expected_source_sha256 and
            rows[0].get('measure_sha256') == MEASURE_SHA and rows[0].get('adb_sha256') == ADB_SHA and
            rows[0].get('deployment_code_sha256') == DEPLOY_SHA, 'Completion provenance drift')
    required = dict(result='OBSERVED_MATCH', matching_boot_chunks=16, wire_request_count=1, wire_opcode=2,
                    source_derived_partition_read_bytes=3804123136, manifest_sha256=MANIFEST,
                    expected_current_p10_sha256=P10, partition_write_requested=False,
                    whole_restore_timing_qualified=False, physical_GO=False, adb_exit_status=0,
                    run_id=binding.run_id, rescue_session_id=binding.rescue_session_id,
                    terminal_evidence=str(directory / 'events.jsonl'))
    require(all(type(result.get(k)) is type(v) and result[k] == v for k, v in required.items()),
            'Completion result mismatch')
    elapsed = result.get('elapsed_seconds')
    require(type(elapsed) in (float, int) and math.isfinite(elapsed) and
            0 <= elapsed <= rows[0]['seconds'] <= 600, 'Invalid measurement interval')
    return result


def observe(binding, live_install_completion_token, *, expected_source_sha256, seconds=180):
    """Future parent API. Never called by CLI; no selection or activation overrides.

    Return must be captured live by parent. A visible evidence file alone is insufficient.
    """
    require(type(seconds) in (int, float) and math.isfinite(seconds) and 0 < seconds <= 600,
            'Finite positive deadline <=600 required')
    require(platform.system() == 'Darwin' and platform.machine() == 'arm64',
            'Pinned local ADB/static CLI analysis is Darwin arm64 only')
    verify_self(expected_source_sha256)
    require(not any(p.is_symlink() for p in (LOCK, *LOCK.parents)), 'Shared lock symlink')
    fd = os.open(LOCK, os.O_RDWR | os.O_NOFOLLOW)
    with os.fdopen(fd, 'r+') as lock:
        require(stat.S_ISREG(os.fstat(fd).st_mode), 'Shared regular mutation lock required')
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        measurement, deployment = load_reviewed()
        check_binding(binding, deployment.host_clock_epoch())
        # This is ONLY the reviewed local historical verifier. No deployment CLI/execute/contract call.
        install, install_sha = deployment.check_install(binding.run_id, DEPLOY_SHA, live_install_completion_token)
        require(install_sha == binding.install_state_sha256, 'Wrong/changed install evidence')
        require(install['pin']['stock']['usb'] == binding.usb_topology, 'Different physical USB topology since install')
        require(binding.created_wall > install['completed_at'], 'Rescue binding predates install')
        require(not any(p.is_symlink() for p in (RUNS, *RUNS.parents)), 'Evidence root symlink')
        RUNS.mkdir(exist_ok=True)
        directory = RUNS / canonical(binding.rescue_session_id)
        directory.mkdir(mode=0o700)  # Exclusive consumption, including failed/uncertain attempts.
        sync_directory(RUNS)
        deadline = time.monotonic() + seconds
        logfd = os.open(directory / 'events.jsonl', os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(logfd, 'w') as log:
            child = None
            try:
                durable(log, dict(result='UNKNOWN', session=dataclasses.asdict(binding),
                                  source_sha256=expected_source_sha256, measure_sha256=MEASURE_SHA,
                                  deployment_code_sha256=DEPLOY_SHA, adb_sha256=ADB_SHA,
                                  seconds=seconds, automatic_retry=False, physical_GO=False))
                sync_directory(directory)
                def guard():
                    require(time.monotonic() < deadline, 'Dispatch deadline expired')
                    verify_self(expected_source_sha256)
                    check_binding(binding, deployment.host_clock_epoch())
                    check_sources()
                    require(sha(read(ADB, 64_000_000)) == ADB_SHA, 'ADB binary drift')
                    # Revalidate nonce, unconsumed install, captures and exact state at actual dispatch.
                    _, current = deployment.check_install(binding.run_id, DEPLOY_SHA, live_install_completion_token)
                    require(current == install_sha, 'Install evidence changed/consumed')
                    require(time.monotonic() < deadline, 'Dispatch checks exhausted deadline')
                    server_version(deadline)
                # Explicit local server endpoint: inherited ADB server/TCP/vendor-key overrides are excluded.
                # Numeric host is intentional: pinned CLI treats this as remote for no-server startup.
                base = [str(ADB), '-H', '127.0.0.1', '-P', '5037']
                selected = base + ['-t', str(binding.transport_id)]
                def inventory():
                    guard()
                    return select_usb(query(base + ['devices', '-l'], deadline), binding)
                inventory()
                guard()
                features = query(selected + ['features'], deadline).decode('ascii').strip().split(',')
                require('shell_v2' in features, 'shell_v2 required; no raw fallback')
                inventory()
                guard()
                def request_guard():
                    # Fresh enumeration after shell creation, before any RSC byte; never reconnect.
                    inventory()
                    guard()
                child = PipeStream(selected + ['shell', '-T', '-e', 'none', 'rescue-v1'], deadline,
                                   before_send=request_guard)
                result = measurement.measure(child, deadline-time.monotonic())
                child.finish()  # EOF and status 0, no trailer tolerated.
                require(time.monotonic() < deadline, 'Whole completion deadline')
                result.update(rescue_session_id=binding.rescue_session_id, run_id=binding.run_id,
                              adb_exit_status=0, stderr_bytes_discarded=child.stderr_bytes,
                              terminal_evidence=str(directory / 'events.jsonl'),
                              commissioning_is_parent_evidence_not_physical_proof=True)
                durable(log, result)
                return result
            except BaseException as error:
                # Exception strings and raw stderr may contain endpoint-controlled token bytes.
                durable(log, dict(result='UNKNOWN', error_type=type(error).__name__,
                                  adb_exit_status=child.proc.poll() if child is not None else None,
                                  stderr_bytes_discarded=child.stderr_bytes if child is not None else 0,
                                  automatic_retry=False, physical_GO=False))
                raise Refused('UNKNOWN; preserve consumed session evidence; no retry') from None
            finally:
                if child is not None:
                    child.dispose()


LOADED_SOURCE_SHA = sha(read(Path(__file__)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    print(json.dumps(dict(mode='PLAN_ONLY', source_sha256=LOADED_SOURCE_SHA, measure_sha256=MEASURE_SHA,
                          deployment_code_sha256=DEPLOY_SHA, adb_path=str(ADB), adb_sha256=ADB_SHA,
                          command=['-t', '<fresh-parent-transport-id>', 'shell', '-T', '-e', 'none', 'rescue-v1'],
                          wire_opcode=2, image_index=1, opens_transport=False, physical_GO=False), sort_keys=True))


if __name__ == '__main__':
    main()
