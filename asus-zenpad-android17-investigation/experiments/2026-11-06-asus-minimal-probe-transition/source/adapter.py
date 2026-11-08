#!/usr/bin/env python3
"""Exact recovery deployment only. Every action is PLAN_ONLY without --execute."""
import argparse
import contextlib
import fcntl
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import secrets
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
RUNS = ROOT / 'evidence/runs'
PROFILE_SHA = '39d0193dfe48acc0d2909120ceea4a9634994408cde5e652be94baeee3fec9e5'
ENGINE_SHA = '630c4aaadbb418dc0af1f5a00628b3ec16117bb165707b4d18794c124464a681'
PRESERVED_SHA = '2035ec23f0797769d949011a6296cb006d0d5ddbd129383a8907f6de6e90b607'
IMAGE_SHA = '535ad86471739967c0e68c058787cf2e5ac6bd844765b75d4bb576200a01d40e'
FULL_SHA = '7562b6168a3cd3f8a2ac4fe1a896f707eab992b2f9b32a1ffb9b1ea33683f596'
PRIOR_FAILED_SHA = '3f99c785cca60bf56c2505711e2d26b72623daf28180515d44c5ba2abf03a44a'
INSTALL_PREIMAGES = ('902b2f06a01cca574b4aa374e67c4e7f8f0ed53f6e6a55017b6d96351f0f1f20', PRIOR_FAILED_SHA)
IMAGE = WORKSPACE / '2026-11-06-asus-minimal-ram-usb-probe/artifacts/candidate.img'
PROFILE = 'asus-p00a-minimal-readonly-ramusb-recovery-deployment-v1'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path, maximum=20_000_000):
    # Reject symlink components as well as a symlink leaf.
    path = Path(path).absolute()
    if any(p.is_symlink() for p in (path, *path.parents)) or not path.is_file():
        raise ValueError('Regular nonsymlink input required: ' + str(path))
    with path.open('rb') as stream:
        data = stream.read(maximum + 1)
    if len(data) > maximum:
        raise ValueError('Oversized input: ' + str(path))
    return data


def load(name, path, pin):
    data = read(path)
    if sha(data) != pin:
        raise ValueError('Pinned engine source changed')
    module = importlib.util.module_from_spec(importlib.util.spec_from_file_location(name, path))
    exec(compile(data, str(path), 'exec'), module.__dict__)
    return module


b = load('exact_stock_engine', ROOT / 'source/engine.py', ENGINE_SHA)
import root_dispatch
require = b.require


def object_sha(value):
    return sha(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode())


def json_file(path):
    def unique(pairs):
        value = {}
        for k, v in pairs:
            require(k not in value, 'Duplicate JSON key')
            value[k] = v
        return value
    return json.loads(read(path, 2_000_000), object_pairs_hook=unique,
                      parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))


def durable(path, value):
    raw = (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n').encode()
    tmp = path.with_suffix('.pending')
    with tmp.open('xb') as out:
        out.write(raw)
        out.flush()
        os.fsync(out.fileno())
    tmp.replace(path)
    fd = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def code_receipt():
    paths = [ROOT / 'profile.json', *sorted((ROOT / 'source').glob('*.py')), ROOT / 'source/preserved.json']
    files = {str(p.relative_to(ROOT)): sha(read(p)) for p in paths}
    return dict(files=files, sha256=object_sha(files))


def check_sources():
    for name, expected in globals().get('LOADED_CODE_FILES', {}).items():
        require(sha(read(ROOT / name)) == expected, 'Loaded/reviewed source drift: ' + name)
    require(sha(read(ROOT / 'profile.json')) == PROFILE_SHA, 'Profile drift')
    require(sha(read(ROOT / 'source/engine.py')) == ENGINE_SHA, 'Engine drift')
    require(sha(read(ROOT / 'source/preserved.json')) == PRESERVED_SHA, 'Provenance manifest drift')
    for path, expected in json_file(ROOT / 'source/preserved.json').items():
        require(sha(read(WORKSPACE / path)) == expected, 'Preserved source drift: ' + path)


def admit(image, stock, full=None):
    p = json_file(ROOT / 'profile.json')
    require(len(image) == 7759872 and sha(image) == IMAGE_SHA, 'Exact minimal readonly RAMUSB probe image required')
    parsed, original = b.unpack_image(image), b.unpack_image(stock)
    require(parsed['end'] == len(image), 'Image boundary mismatch')
    require(list(parsed['header']) == p['image']['header'], 'Header/layout mismatch')
    require(sha(image[:2048]) == p['image']['header_page_sha256'], 'Header page mismatch')
    require(parsed['kernel'] == original['kernel'] and sha(parsed['kernel']) == b.KERNEL_HASH,
            'Exact wrapped stock kernel required')
    require(all(parsed['header'][i] == original['header'][i] for i in (0, 1, 3, 4, 5, 6, 7, 8, 9)),
            'Stock geometry/header addresses changed')
    expected = image + bytes(b.SIZE - len(image))
    full = expected if full is None else full
    require(len(full) == b.SIZE and full == expected and sha(full) == FULL_SHA, 'Full p10/padding mismatch')
    return full


def verify_local():
    check_sources()
    stock, records = b.local_inputs()
    image = read(IMAGE)
    full = admit(image, stock)
    return stock, full, dict(profile=PROFILE, profile_sha256=PROFILE_SHA, code=code_receipt(),
                            inputs=records + [dict(path=str(IMAGE), bytes=len(image), sha256=sha(image))],
                            candidate_sha256=IMAGE_SHA, full_p10_sha256=FULL_SHA,
                            device_contacted=False, physical_GO=False, hardware_ready=False,
                            target_is_zero_record=False, bounded_automatic_return_claim=False)


def canonical(run):
    require(isinstance(run, str) and str(uuid.UUID(run)) == run, 'Canonical run UUID required')
    return run


def finite(value):
    return type(value) in (float, int) and math.isfinite(value)


def host_clock_epoch():
    """Bind a persisted monotonic timestamp to this host's current boot."""
    if sys.platform.startswith('linux'):
        value = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
        platform = 'linux'
    elif sys.platform == 'darwin':
        import ctypes
        libc = ctypes.CDLL(None, use_errno=True)
        query = libc.sysctlbyname
        query.argtypes = [ctypes.c_char_p, ctypes.c_void_p, ctypes.POINTER(ctypes.c_size_t),
                          ctypes.c_void_p, ctypes.c_size_t]
        query.restype = ctypes.c_int
        size = ctypes.c_size_t()
        require(query(b'kern.bootsessionuuid', None, ctypes.byref(size), None, 0) == 0 and
                0 < size.value <= 128, 'Host boot epoch unavailable')
        buffer = ctypes.create_string_buffer(size.value)
        require(query(b'kern.bootsessionuuid', buffer, ctypes.byref(size), None, 0) == 0,
                'Host boot epoch query failed')
        value = buffer.value.decode('ascii').lower()
        platform = 'darwin'
    else:
        raise b.Refused('Unsupported host monotonic clock epoch')
    require(str(uuid.UUID(value)) == value, 'Invalid host boot epoch')
    return platform + ':' + value


PROPS = {'ro.serialno': b.SERIAL, 'ro.product.device': 'P00A_2', 'ro.product.name': 'WW_P00A',
         'ro.product.model': 'P00A', 'ro.build.version.sdk': '24', 'ro.build.fingerprint': b.FINGERPRINT,
         'sys.boot_completed': '1', 'ro.adb.secure': '1', 'init.svc.flash_recovery': 'stopped'}


def select(text):
    rows = []
    for line in text.splitlines():
        if not line or line == 'List of devices attached':
            continue
        words = line.split()
        require(len(words) >= 2 and not words[0].startswith('*'), 'Malformed inventory')
        row = dict(serial=words[0], state=words[1])
        for field in words[2:]:
            require(':' in field, 'Malformed inventory field')
            k, v = field.split(':', 1)
            require(k not in row and v, 'Duplicate/empty inventory field')
            row[k] = v
        rows.append(row)
    require(len({r['serial'] for r in rows}) == len(rows), 'Duplicate serial')
    ids = [r.get('transport_id') for r in rows]
    require(all(ids) and len(set(ids)) == len(ids), 'Missing/duplicate transport ID')
    candidates = [r for r in rows if 'usb' in r or r['serial'] == b.SERIAL]
    require(len(candidates) == 1, 'Require one unambiguous physical USB device')
    row = candidates[0]
    require(all(row.get(k) == v for k, v in dict(serial=b.SERIAL, state='device', product='WW_P00A',
                                               model='P00A', device='P00A_2').items()), 'Wrong USB identity/state')
    require(re.fullmatch('[0-9A-Za-z.:_-]+', row.get('usb', '')) and
            re.fullmatch('[1-9][0-9]*', row.get('transport_id', '')), 'Invalid USB topology/transport ID')
    tcp = [r for r in rows if r['serial'] == b.ENDPOINT]
    require(len(tcp) == 1 and tcp[0]['state'] == 'device', 'Fixed authenticated Wi-Fi must already be connected')
    return row


def validate_pin_binding(pin, run, code):
    """Check historical identity only; never grants freshness for dispatch."""
    require(pin.get('schema') == 2 and pin.get('run_id') == canonical(run) and pin.get('profile') == PROFILE and
            pin.get('code_sha256') == code and pin.get('candidate_sha256') == IMAGE_SHA and
            pin.get('full_p10_sha256') == FULL_SHA, 'Pin run/code/image binding mismatch')
    require(finite(pin.get('created_at')) and finite(pin.get('created_monotonic')) and
            pin['created_monotonic'] >= 0 and isinstance(pin.get('host_clock_epoch'), str) and
            re.fullmatch(r'(?:darwin|linux):[0-9a-f-]{36}', pin['host_clock_epoch']),
            'Pin host clock binding missing or invalid')
    require(pin.get('properties') == PROPS and pin.get('enforcing') is True, 'Healthy stock pin required')
    require(re.fullmatch('[0-9a-f-]{36}', pin.get('boot_id', '')) and
            str(uuid.UUID(pin['boot_id'])) == pin['boot_id'], 'Stock boot UUID required')
    row = pin['stock']
    require(all(row.get(k) == v for k, v in dict(serial=b.SERIAL, state='device', product='WW_P00A',
                                               model='P00A', device='P00A_2').items()), 'Pin USB identity mismatch')
    require(re.fullmatch('[0-9A-Za-z.:_-]+', row.get('usb', '')) and
            re.fullmatch('[1-9][0-9]*', row.get('transport_id', '')), 'Invalid pin topology')


def validate_pin(pin, run, code, now=None):
    validate_pin_binding(pin, run, code)
    require(pin['host_clock_epoch'] == host_clock_epoch(), 'Pin belongs to another host boot epoch')
    now = time.time() if now is None else now
    mono = time.monotonic()
    require(0 <= now - pin['created_at'] <= 180 and
            0 <= mono - pin['created_monotonic'] <= 180, 'Stale/future wall or monotonic pin')


def contract_template(run, phase):
    return dict(schema=1, run_id=canonical(run), phase=phase, profile_sha256=PROFILE_SHA,
                code_sha256=code_receipt()['sha256'], parent_technical_review=False, reviewer='', reference='',
                issued_at=None, valid_until=None, maximum_seconds=600,
                supervised_manual_entry_return_plan=False, nearby_power_fallback_required=True,
                install_completion_token=None)


class Guard:
    def __init__(self, contract, run, phase, code, pin=None):
        require(contract.get('schema') == 1 and contract.get('run_id') == canonical(run) and
                contract.get('phase') == phase and contract.get('profile_sha256') == PROFILE_SHA and
                contract.get('code_sha256') == code, 'Contract binding mismatch')
        require(contract.get('parent_technical_review') is True and
                contract.get('supervised_manual_entry_return_plan') is True and
                contract.get('nearby_power_fallback_required') is True and
                all(isinstance(contract.get(k), str) and contract[k].strip() for k in ('reviewer', 'reference')),
                'Parent technical review and manual supervision contract required')
        now = time.time()
        start, end = contract.get('issued_at'), contract.get('valid_until')
        require(finite(start) and finite(end) and start <= now < end and 0 < end-start <= 600 and
                contract.get('maximum_seconds') == 600, 'Fresh bounded per-phase contract required')
        self.contract, self.run, self.code, self.pin = contract, run, code, pin
        self.end_mono = time.monotonic() + (end - now)
        self.stopped = False
        self.check()

    def check(self):
        if self.stopped:
            raise b.UncertainTransport('Terminal stop latched; no further commands')
        try:
            require(self.contract['issued_at'] <= time.time() < self.contract['valid_until'] and
                    time.monotonic() < self.end_mono, 'Run deadline expired')
            check_sources()
            require(code_receipt()['sha256'] == self.code, 'Reviewed adapter source drift')
            if self.pin is not None:
                validate_pin(self.pin, self.run, self.code)
                self.end_mono = min(self.end_mono, self.pin['created_monotonic'] + 180)
            # Source/evidence reads may themselves consume the last part of the window.
            require(self.contract['issued_at'] <= time.time() < self.contract['valid_until'] and
                    time.monotonic() < self.end_mono, 'Run deadline expired at actual dispatch boundary')
        except (b.Refused, ValueError, KeyError, TypeError, OSError) as exc:
            self.stopped = True
            raise b.UncertainTransport('Authorization invalid; stop all commands: ' + str(exc)) from exc


@contextlib.contextmanager
def mutation_lock():
    # Open only the existing shared host lock, never create an alternate lock.
    with b.EXECUTE_LOCK.open('r+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


def reserve(run, phase):
    canonical(run)
    require(phase in ('pin-install', 'install', 'pin-restore', 'restore'), 'Invalid phase')
    parent = RUNS / run
    require(not any(p.is_symlink() for p in (parent, *parent.parents)), 'Symlink run path')
    parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    directory = parent / phase
    directory.mkdir(mode=0o700, exist_ok=False)
    return directory


class Journal(b.Journal):
    def __init__(self, directory, phase, run, code):
        self.directory = directory
        self.state = dict(schema=1, mode='EXECUTE', run_id=run, phase=phase, profile=PROFILE,
                          profile_sha256=PROFILE_SHA, code_sha256=code, candidate_sha256=IMAGE_SHA,
                          full_p10_sha256=FULL_SHA, started_at=time.time(), events=[], commands=[], captures=[],
                          write_dispatches=[], outcome='preparing', partition_status='not_observed',
                          partition_may_be_modified=True, restore_verified=False, cleanup='not_attempted',
                          manual_entered=False, probe_report_observed=False, stock_returned=False,
                          manual_recovery_permitted=False, hardware_ready=False, physical_GO=False)
        self.save()

    def save(self):
        try:
            durable(self.directory / 'state.json', self.state)
        except (OSError, ValueError) as exc:
            raise b.UncertainTransport('Evidence persistence failed; no later commands') from exc

    def finish(self, outcome, **kwargs):
        return super().finish(outcome, completed_at=time.time(), **kwargs)

    def observed(self, data):
        h = sha(data)
        self.state.update(partition_status='exact_stock' if h == b.STOCK_HASH else
                          'exact_candidate' if h == FULL_SHA else
                          'exact_prior_failed_rescue' if h == PRIOR_FAILED_SHA else 'unexpected_bytes',
                          partition_may_be_modified=(h != b.STOCK_HASH))
        self.save()


class Transport(b.AdbRootTransport):
    def __init__(self, directory, journal, phase, guard):
        super().__init__(directory, journal, 'install' if phase.endswith('install') else 'restore')
        self.phase, self.guard = phase, guard
        self.session = b.BASE + '/exact-ramusb-' + guard.run + '-' + phase
        self.vault, self.inbox = self.session + '/vault', self.session + '/inbox'
        self.pending_kind = None
        self.last_root = None
        self.last_command = None

    def stop(self, message):
        self.guard.stopped = True
        raise b.UncertainTransport(message)

    def low_command(self, argv, *, script=None, timeout=90, usb_guard=True):
        self.guard.check()
        # Every nested Wi-Fi request checks current physical enumeration too.
        if usb_guard and self.guard.pin is not None:
            self.usb_enumeration()
        self.sequence += 1
        path = self.directory / f'command-{self.sequence:04}.json'
        record = dict(argv=argv, stdin=script, status='intent', at=time.time())
        prior_partition = (self.journal.state['partition_status'], self.journal.state['partition_may_be_modified'])
        write_intent = None
        sent = False
        try:
            durable(path, record)
            self.journal.state['commands'].append(path.name)
            self.journal.save()
            is_root = argv[3:4] == ['shell'] and len(argv) == 5 and argv[-1].startswith('timeout 60 ')
            if is_root and self.pending_kind:
                kind = self.pending_kind
                previous = [x['source'] for x in self.journal.state['write_dispatches']]
                require(kind not in previous and (kind != 'candidate' or not previous), 'Write attempt already consumed')
                write_intent = dict(source=kind, target=b.BLOCK, command=path.name, delivery='intent_completion_untrusted')
                self.journal.state['write_dispatches'].append(write_intent)
                self.journal.state.update(partition_status='write_completion_pending', partition_may_be_modified=True)
                self.journal.save()
            # Crucially AFTER evidence writes, immediately before the actual nested dispatch.
            self.guard.check()
            sent = True
            result = subprocess.run(argv, input=script, text=True, capture_output=True,
                                    timeout=min(timeout, self.guard.end_mono - time.monotonic()))
            record.update(status='returned', exit_status=result.returncode, stdout=result.stdout, stderr=result.stderr,
                          completed_at=time.time())
            durable(path.with_name(path.stem + '-result.json'), record)
            self.last_command = path
            if result.returncode:
                self.stop('ADB/helper request nonzero; completion untrusted')
            self.guard.check()  # Late completion cannot authorize cleanup/inverse.
            if is_root:
                self.last_root = path
            return result
        except (subprocess.TimeoutExpired, OSError, UnicodeError, ValueError, b.Refused, b.UncertainTransport) as exc:
            self.guard.stopped = True
            if write_intent is not None and not sent:
                write_intent['delivery'] = 'not_dispatched_run_consumed'
                self.journal.state.update(partition_status=prior_partition[0], partition_may_be_modified=prior_partition[1])
                try:
                    self.journal.save()
                except b.UncertainTransport:
                    pass
            try:
                durable(path.with_name(path.stem + '-uncertain.json'), dict(
                    status='uncertain', error=str(exc), partition_status=self.journal.state['partition_status'],
                    partial_stdout_hex=getattr(exc, 'stdout', b'').hex() if isinstance(getattr(exc, 'stdout', None), bytes) else None,
                    partial_stderr_hex=getattr(exc, 'stderr', b'').hex() if isinstance(getattr(exc, 'stderr', None), bytes) else None,
                    partial_stdout=getattr(exc, 'stdout', None) if isinstance(getattr(exc, 'stdout', None), str) else None,
                    partial_stderr=getattr(exc, 'stderr', None) if isinstance(getattr(exc, 'stderr', None), str) else None))
            except (OSError, ValueError):
                pass
            raise b.UncertainTransport('Command boundary stopped: ' + str(exc)) from exc

    def command(self, argv, *, script=None, timeout=90):
        if argv == [sys.executable, str(b.HELPER)]:
            try:
                result = root_dispatch.run(b, script, self.low_command)
                self.journal.event('pinned_helper_completion', stdout=result.stdout, stderr=result.stderr,
                                   helper_exit_status=result.returncode)
                return result
            except (b.UncertainTransport, b.Refused, UnicodeError, OSError) as exc:
                self.stop(str(exc))
        return self.low_command(argv, script=script, timeout=timeout)

    def usb_enumeration(self):
        try:
            result = self.low_command(['adb', 'devices', '-l'], timeout=12, usb_guard=False)
            require(not result.stderr, 'USB inventory error')
            row = select(result.stdout)
            if self.guard.pin is not None:
                require(row == self.guard.pin['stock'], 'Current USB topology/identity/transport changed')
            return row
        except (b.Refused, ValueError, KeyError, UnicodeError) as exc:
            self.stop('USB identity unavailable: ' + str(exc))

    def usb_snapshot(self):
        # Charge the whole observation interval to pin age, not only publication.
        created_at, created_monotonic = time.time(), time.monotonic()
        clock_epoch = host_clock_epoch()
        row = self.usb_enumeration()
        def query(args):
            result = self.low_command(['adb', '-t', row['transport_id'], *args], timeout=12, usb_guard=False)
            require(not result.stderr, 'USB query error')
            return result.stdout.strip()
        try:
            props = {k: query(['shell', 'getprop', k]) for k in PROPS}
            require(props == PROPS and query(['shell', 'getenforce']) == 'Enforcing', 'Unhealthy stock USB identity')
            boot_id = query(['shell', 'cat', '/proc/sys/kernel/random/boot_id'])
            require(str(uuid.UUID(boot_id)) == boot_id, 'Invalid current boot identity')
            require(self.usb_enumeration() == row, 'USB changed during stock snapshot')
            if self.guard.pin is not None:
                require(boot_id == self.guard.pin['boot_id'], 'Stock boot changed during phase')
            return dict(schema=2, profile=PROFILE, run_id=self.guard.run, code_sha256=self.guard.code,
                        candidate_sha256=IMAGE_SHA, full_p10_sha256=FULL_SHA, created_at=created_at,
                        created_monotonic=created_monotonic, host_clock_epoch=clock_epoch,
                        stock=row, properties=props, boot_id=boot_id, enforcing=True)
        except (b.Refused, ValueError, KeyError, UnicodeError) as exc:
            self.stop('USB health/identity unavailable: ' + str(exc))

    def healthy(self):
        self.usb_snapshot()
        try:
            super().healthy()
            require(self.adb(['shell', 'cat', '/proc/sys/kernel/random/boot_id']) == self.guard.pin['boot_id'],
                    'Wi-Fi and USB boot identities differ')
            require(self.adb(['shell', 'getprop', 'init.svc.flash_recovery']) == 'stopped', 'Stock autorepair running')
        except b.Refused as exc:
            self.stop('Stock health unavailable: ' + str(exc))

    def root(self, body, label):
        self.guard.check()
        boot = self.guard.pin['boot_id']
        fixed = f'''[ "$(cat /proc/sys/kernel/random/boot_id)" = '{boot}' ]
[ "$(getprop init.svc.flash_recovery)" = stopped ]'''
        # Retain mandatory token, exact node/alias/geometry and pinned-helper guards.
        return super().root(fixed + '\n' + body, label)

    def pull(self, label):
        root = self.last_root
        data = super().pull(label)
        if label == 'recovery':
            require(root is not None, 'Missing physical read command')
            capture = dict(source=b.BLOCK, session=self.session, bytes=len(data), sha256=sha(data),
                           run_id=self.guard.run, pin_sha256=object_sha(self.guard.pin), at=time.time(),
                           file=Path(self.journal.state['events'][-1]['path']).name)
            for name, path in (('root', root), ('pull', self.last_command)):
                result_path = path.with_name(path.stem + '-result.json')
                capture[name + '_intent'] = dict(file=path.name, sha256=sha(read(path)))
                capture[name + '_completion'] = dict(file=result_path.name, sha256=sha(read(result_path)))
            self.journal.state['captures'].append(capture)
            self.journal.observed(data)
        return data

    def cleanup(self):
        self.guard.check()
        return super().cleanup()

    def write(self, kind):
        self.guard.check()
        self.pending_kind = kind
        try:
            return super().write(kind)
        finally:
            self.pending_kind = None


def verify_capture(directory, state, expected, index=-1):
    require(bool(state.get('captures')), 'No actual guarded partition capture')
    capture = state['captures'][index]
    require(capture['source'] == b.BLOCK and capture['run_id'] == state['run_id'] and
            capture['pin_sha256'] == object_sha(state['pin']) and capture['bytes'] == b.SIZE and
            capture['sha256'] == expected and state['started_at'] <= capture['at'] <= state['completed_at'],
            'Capture binding/chronology mismatch')
    def local_file(name):
        require(isinstance(name, str) and Path(name).name == name, 'Unsafe evidence filename')
        return directory / name
    data = read(local_file(capture['file']))
    require(len(data) == b.SIZE and sha(data) == expected, 'Full capture drift')
    records = {}
    for key in ('root_intent', 'root_completion', 'pull_intent', 'pull_completion'):
        entry = capture[key]
        path = local_file(entry['file'])
        require(sha(read(path)) == entry['sha256'], 'Capture command provenance drift')
        records[key] = json_file(path)
    root, pull = records['root_intent'], records['pull_intent']
    result = records['root_completion']
    require(root['argv'] == ['adb', '-s', b.ENDPOINT, 'shell',
                            'timeout 60 /data/local/tmp/asus-mtk-su64 -c /system/bin/sh'], 'Unpinned root capture')
    expected_read = f"dd if={b.BLOCK} of={capture['session']}/vault/readback.bin bs=512 count={b.SECTORS}"
    require(expected_read in root['stdin'] and b.DEVICE_GUARD in root['stdin'] and
            not re.search(r'dd if=\S+ of=' + re.escape(b.BLOCK), root['stdin']), 'Not a guarded physical full p10 read')
    tokens = re.findall(r'ASUS_RECOVERY_RC_([0-9a-f]{32})=', root['stdin'])
    require(len(tokens) == 1 and result['status'] == 'returned' and result['exit_status'] == 0 and
            b.root_status(subprocess.CompletedProcess(root['argv'], result['exit_status'],
                                                      result['stdout'], result['stderr']), tokens[0]) == 0,
            'Incomplete root capture status')
    require(pull['argv'] == ['adb', '-s', b.ENDPOINT, 'pull', capture['session'] + '/inbox/readback.bin',
                            str(local_file(capture['file']))] and
            records['pull_completion']['status'] == 'returned' and
            records['pull_completion']['exit_status'] == 0, 'Not a completed linked full readback pull')
    return capture


def check_install(run, code, completion_token=None):
    directory = RUNS / canonical(run) / 'install'
    state = json_file(directory / 'state.json')
    require(isinstance(completion_token, str) and re.fullmatch('[0-9a-f]{64}', completion_token) and
            sha(completion_token.encode()) == state.get('live_completion_token_sha256'),
            'Successful live install return required; visible journal cannot reconstruct lost completion')
    require(state.get('mode') == 'EXECUTE' and state.get('run_id') == run and state.get('profile') == PROFILE and
            state.get('code_sha256') == code and state.get('profile_sha256') == PROFILE_SHA and
            state.get('candidate_sha256') == IMAGE_SHA and state.get('full_p10_sha256') == FULL_SHA,
            'Install source/profile linkage mismatch')
    require(state.get('outcome') == 'installed_full_hash_verified' and state.get('cleanup') == 'verified' and
            state.get('partition_status') == 'exact_candidate', 'No clean install; failed/uncertain/consumed runs stop')
    require([x['source'] for x in state.get('write_dispatches', [])] == ['candidate'], 'Install already used inverse')
    # This old pin proves install linkage only. load_pin() and Guard.check()
    # independently require a fresh current pin before any new dispatch.
    validate_pin_binding(state['pin'], run, code)
    require(len(state.get('captures', [])) >= 2, 'Missing physical allowed preimage capture')
    preimage = state.get('install_preimage_sha256')
    require(preimage in INSTALL_PREIMAGES and state.get('install_preimage_bytes') == b.SIZE,
            'Missing exact complete allowed install preimage binding')
    before = verify_capture(directory, state, preimage, index=0)
    after = verify_capture(directory, state, FULL_SHA)
    write_name = state['write_dispatches'][0]['command']
    require(Path(write_name).name == write_name, 'Unsafe write evidence filename')
    write = json_file(directory / write_name)
    require(before['at'] <= write['at'] <= after['at'], 'Allowed preimage/write/readback chronology mismatch')
    require(not (RUNS / run / 'restore').exists(), 'Restore phase already consumed; no retry/resume')
    return state, sha(read(directory / 'state.json'))


def load_pin(run, action, code, install=None):
    directory = RUNS / canonical(run) / ('pin-' + action)
    state = json_file(directory / 'state.json')
    require(state.get('outcome') == 'healthy_stock_usb_pin_captured' and state.get('mode') == 'EXECUTE' and
            state.get('code_sha256') == code and state.get('run_id') == run and
            state.get('phase') == 'pin-' + action and state.get('profile_sha256') == PROFILE_SHA,
            'Missing actual same-run preflight linkage')
    pin = json_file(directory / 'pin.json')
    require(state.get('pin_sha256') == object_sha(pin), 'Pin receipt drift')
    validate_pin(pin, run, code)
    # Command/result pairs, rather than copied backup bytes, bind this actual observation.
    require(len(state.get('commands', [])) >= len(PROPS) + 4, 'Incomplete USB capture provenance')
    for name in state['commands']:
        require(Path(name).name == name, 'Unsafe preflight command file')
        intent = json_file(directory / name)
        result = json_file(directory / (Path(name).stem + '-result.json'))
        require(intent['argv'][:2] in (['adb', 'devices'], ['adb', '-t']) and
                result['argv'] == intent['argv'] and result['status'] == 'returned' and
                result['exit_status'] == 0, 'Incomplete preflight request')
    if install:
        old, new = install['pin']['stock'], pin['stock']
        require({k:v for k,v in old.items() if k != 'transport_id'} ==
                {k:v for k,v in new.items() if k != 'transport_id'}, 'USB physical topology/identity changed since install')
        require(pin['created_at'] > install['completed_at'], 'Restore requires fresh current stock pin after install/manual return')
    return pin


def execute(action, stock, candidate, t, j):
    """Only a known candidate completion failure can enter the single bounded inverse."""
    def verified_stock():
        data = t.read()
        if len(data) != b.SIZE or sha(data) != b.STOCK_HASH:
            raise b.VerificationFailed('Full stock inverse readback mismatch')
        t.healthy()
        j.state['restore_verified'] = True
        j.save()

    try:
        t.healthy()
        t.setup()
        t.stage('stock', stock)
        if action == 'install':
            t.stage('candidate', candidate)
        before = t.read()
        if action == 'install':
            require(len(before) == b.SIZE and sha(before) in INSTALL_PREIMAGES,
                    'Install requires one exact complete allowed physical p10 preimage')
            j.state.update(install_preimage_sha256=sha(before), install_preimage_bytes=len(before))
            j.save()
            t.healthy()
            t.write('candidate')
            data = t.read()
            if len(data) != b.SIZE or sha(data) != FULL_SHA:
                raise b.VerificationFailed('Full installed candidate readback mismatch')
            t.healthy()
            outcome = 'installed_full_hash_verified'
        else:
            # Never replace arbitrary unexpected recovery bytes in a later restore phase.
            require(sha(before) in (FULL_SHA, b.STOCK_HASH), 'Unexpected recovery hash; restore refused')
            t.healthy()
            if sha(before) == b.STOCK_HASH:
                j.state['restore_verified'] = True
                outcome = 'verified_already_original'
            else:
                t.write('stock')
                verified_stock()
                outcome = 'restored_full_hash_verified'
    except b.UncertainTransport as exc:
        t.guard.stopped = True
        return j.finish('terminal_uncertainty_no_commands', error=str(exc))
    except (b.Refused, b.OperationFailed, b.VerificationFailed, OSError, ValueError) as exc:
        candidate_sent = [x['source'] for x in j.state['write_dispatches']] == ['candidate']
        if action != 'install' or not candidate_sent:
            return j.finish('refused_or_failed_stop', error=str(exc))
        try:
            t.guard.check()
            t.healthy()
            current = t.read()
            if sha(current) == b.STOCK_HASH:
                j.state['restore_verified'] = True
                outcome = 'install_failed_already_original_verified'
            else:
                t.write('stock')
                verified_stock()
                outcome = 'install_failed_fixed_inverse_verified'
        except (b.Refused, b.OperationFailed, b.VerificationFailed, b.UncertainTransport, OSError, ValueError) as inverse:
            t.guard.stopped = True
            return j.finish('inverse_unverified_stop', error=str(exc), inverse_error=str(inverse))
    # Only a valid, known complete phase may attempt cleanup, never after uncertainty/expiry.
    try:
        t.guard.check()
        t.cleanup()
        t.healthy()
        return j.finish(outcome, cleanup='verified')
    except (b.Refused, b.OperationFailed, b.VerificationFailed, b.UncertainTransport, OSError, ValueError) as exc:
        t.guard.stopped = True
        return j.finish(outcome, cleanup='unverified', cleanup_error=str(exc))


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=('verify-local', 'plan', 'template', 'pin-install', 'install', 'pin-restore', 'restore'))
    p.add_argument('--execute', action='store_true')
    p.add_argument('--run-id')
    p.add_argument('--phase', choices=('pin-install', 'install', 'pin-restore', 'restore'))
    p.add_argument('--contract', type=Path)
    p.add_argument('--supervised', action='store_true')
    p.add_argument('--physical-fallback-present', action='store_true')
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    journal = None
    guard = None
    os.umask(0o077)
    try:
        stock, full, local = verify_local()
        if args.action == 'template':
            require(not args.execute and args.phase is not None, 'Template is offline and requires --phase')
            print(json.dumps(contract_template(args.run_id, args.phase), indent=2))
            return 0
        if not args.execute:
            print(json.dumps(dict(mode='PLAN_ONLY', action=args.action, **local,
                                  actual_actions_executed=False, manual_recovery_permitted=False,
                                  gates=['parent technical code/profile review', 'fresh per-phase bounded contract',
                                         'current supervision and nearby Power fallback', 'fresh same-run USB pin',
                                         'shared mutation lock', 'separately parent-owned manual entry/return']), indent=2))
            return 0
        require(args.action in ('pin-install', 'install', 'pin-restore', 'restore'), 'Offline action cannot execute')
        require(args.supervised and args.physical_fallback_present,
                'Execute needs actual current supervision and nearby Power fallback; implementation asserts neither')
        run = canonical(args.run_id)
        require(args.contract is not None and ROOT in args.contract.absolute().parents, 'Owned per-phase contract required')
        contract = json_file(args.contract)
        code = local['code']['sha256']
        guard = Guard(contract, run, args.action, code)
        with mutation_lock():
            install, linkage = check_install(run, code, contract.get('install_completion_token')) if args.action in ('pin-restore', 'restore') else (None, None)
            if args.action == 'pin-install':
                require(not (RUNS / run / 'install').exists(), 'Install run already consumed')
            pin = None if args.action.startswith('pin-') else load_pin(run, args.action, code, install)
            guard.pin = pin
            guard.check()
            directory = reserve(run, args.action)
            journal = Journal(directory, args.action, run, code)
            journal.state.update(contract=contract, contract_sha256=object_sha(contract), pin=pin,
                                 install_journal_sha256=linkage, local_inputs=local['inputs'],
                                 supervision_attested=True, nearby_fallback_attested=True,
                                 attestations_are_not_physical_proof=True)
            journal.save()
            t = Transport(directory, journal, args.action, guard)
            if args.action.startswith('pin-'):
                pin = t.usb_snapshot()
                if install:
                    require({k:v for k,v in pin['stock'].items() if k != 'transport_id'} ==
                            {k:v for k,v in install['pin']['stock'].items() if k != 'transport_id'},
                            'Restore USB physical topology/identity changed')
                durable(directory / 'pin.json', pin)
                state = journal.finish('healthy_stock_usb_pin_captured', pin=pin, pin_sha256=object_sha(pin))
            else:
                state = execute(args.action, stock, full, t, journal)
            completion = None
            if args.action == 'install' and state['outcome'] == 'installed_full_hash_verified' and state['cleanup'] == 'verified':
                # Only the successful live API return reveals this receipt nonce.
                # A visible renamed journal after failed fsync cannot authorize a later phase.
                completion = secrets.token_hex(32)
                state = journal.finish(state['outcome'], live_completion_token_sha256=sha(completion.encode()))
            print(json.dumps(dict(outcome=state['outcome'], evidence=str(directory),
                                  install_completion_token=completion,
                                  partition_status=state['partition_status'],
                                  partition_may_be_modified=state['partition_may_be_modified'],
                                  manual_recovery_permitted=False, hardware_ready=False), indent=2))
            return 0 if state['outcome'] in ('healthy_stock_usb_pin_captured', 'installed_full_hash_verified',
                                             'restored_full_hash_verified', 'verified_already_original') and state.get('cleanup') != 'unverified' else 2
    except (b.Refused, b.UncertainTransport, ValueError, KeyError, TypeError, OSError, UnicodeError) as exc:
        if guard:
            guard.stopped = True
        if journal:
            try:
                journal.finish('terminal_refusal_or_uncertainty', error=str(exc))
            except (b.UncertainTransport, OSError):
                pass
        print(json.dumps(dict(outcome='refused', error=str(exc), hardware_ready=False)), file=sys.stderr)
        return 2


# Bind the actual loaded code to the on-disk review receipt for this process.
LOADED_CODE_FILES = code_receipt()['files']


if __name__ == '__main__':
    raise SystemExit(main())
