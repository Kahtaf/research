#!/usr/bin/env python3
"""Frozen P00A49PROBE transport. PLAN_ONLY unless explicitly supervised."""
import argparse
import contextlib
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
PROFILE_FILE = ROOT / 'profile.json'
PROFILE_SHA = '33545e535bc5a3ce23edc09d7b36b5bd7a601c6cdb549c7f8d91da2ce4e558bd'
BASE_SHA = 'f5f2070d4ed328b046a59e7d08b66af5ffb960a3a2b299e1a583e7c4ab757de4'
OBSERVER_PATH = WORKSPACE / '2026-11-06-asus-linux49-probe-acceptance/source/observer.py'
OBSERVER_SHA = '75b1d96686a484e0eb5cfd73ec62976c394de1895e14ea45c83ea745d15f07ec'
KERNEL = WORKSPACE / '2026-11-06-asus-android17-build-continuation/artifacts/Image.gz-dtb-combined-r1'
KERNEL_SHA = 'd4094bcff6c763af7f1c01ccd3d612a988f96de13f78b492b808cc76c0ac929f'


def digest(data):
    import hashlib
    return hashlib.sha256(data).hexdigest()


def load_pinned(name, path, expected):
    if path.is_symlink() or digest(path.read_bytes()) != expected:
        raise RuntimeError('Pinned source changed: ' + str(path))
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


b = load_pinned('probe_base', ROOT / 'source/recovery_control.py', BASE_SHA)
o = load_pinned('probe_observer', OBSERVER_PATH, OBSERVER_SHA)
require = b.require
RUNS = ROOT / 'evidence/runs'


def json_file(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, 'Duplicate JSON field')
            result[key] = value
        return result
    return json.loads(b.read_bounded(path, 2_000_000), object_pairs_hook=unique)


def canonical_run(run):
    require(run is not None and str(uuid.UUID(run)) == run, 'Canonical run UUID required')
    return run


def code_receipt():
    files = {str(p.relative_to(ROOT)): digest(b.read_bounded(p)) for p in
             (ROOT / 'source/probe_transport.py', ROOT / 'source/recovery_control.py', PROFILE_FILE)}
    files['parent_observer'] = digest(b.read_bounded(OBSERVER_PATH))
    return dict(files=files, sha256=o.object_sha(files))


def verify_local():
    require(digest(b.read_bounded(PROFILE_FILE)) == PROFILE_SHA, 'Exact profile changed')
    profile = json_file(PROFILE_FILE)
    stock, records = b.local_inputs()
    image = b.read_bounded(o.IMAGE)
    require(len(image) == 8880128 and digest(image) == o.IMAGE_SHA, 'Frozen r2 candidate changed')
    full = image + bytes(b.SIZE - len(image))
    require(digest(full) == o.PADDED_SHA, 'Frozen full p10 padding changed')
    kernel = b.read_bounded(KERNEL)
    require(len(kernel) == 7696186 and digest(kernel) == KERNEL_SHA, 'Exact combined-r1 kernel input changed; product r3 forbidden')
    parsed = b.unpack_image(image)
    require(parsed['end'] == len(image), 'Image boundary changed')
    require(digest(image[:2048]) == profile['candidate']['header_page_sha256'], 'Header changed')
    # The reviewed compressed Image is unchanged. Only the three chosen DT properties
    # differ from the input; the exact whole-image pin also binds the packaged DT.
    compressed_size = 7632565
    require(digest(parsed['kernel'][512:512 + compressed_size]) == profile['kernel']['compressed_image_sha256'], 'Compressed Image changed')
    require(digest(parsed['kernel'][512 + compressed_size:]) == profile['kernel']['packaged_dtb_sha256'], 'Packaged DT changed')
    require(digest(parsed['ramdisk'][512:]) == profile['ramdisk']['gzip_sha256'], 'Ramdisk changed')
    records += [dict(path=str(o.IMAGE), bytes=len(image), sha256=digest(image)),
                dict(path=str(KERNEL), bytes=len(kernel), sha256=digest(kernel))]
    return stock, full, dict(profile=profile, profile_sha256=PROFILE_SHA, code=code_receipt(),
                            inputs=records, hardware_ready=False, device_contacted=False)


def validate_pin(pin, run, now=None):
    try:
        o.validate_pin(pin, canonical_run(run), now=now)
    except o.Refused as exc:
        raise b.Refused(str(exc)) from exc
    require(pin['stock'].get('product') == 'WW_P00A' and pin['stock'].get('model') == 'P00A',
            'Exact stock USB product/model required')


@contextlib.contextmanager
def mutation_lock():
    # Never create a different lock when the shared lock is unavailable.
    with b.EXECUTE_LOCK.open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


def reserve(run, action):
    canonical_run(run)
    require(action in ('install', 'restore', 'readback', 'finalize'), 'Invalid phase')
    directory = RUNS / run / action
    require(ROOT in directory.resolve().parents and not directory.is_symlink(), 'Unsafe output path')
    directory.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    directory.mkdir(mode=0o700, exist_ok=False)  # No retry/resume, even after interruption.
    return directory


class Journal(b.Journal):
    def __init__(self, directory, action, run, pin, reviewed, mode='EXECUTE'):
        super().__init__(directory, action, mode)
        self.state.update(schema=1, run_id=run, profile=o.PROFILE, candidate_sha256=o.IMAGE_SHA,
                          padded_sha256=o.PADDED_SHA, profile_sha256=PROFILE_SHA,
                          code_sha256=code_receipt()['sha256'], pin=pin, pin_sha256=o.object_sha(pin),
                          started_at=time.time(), reviewed=reviewed, captures=[], command_receipts=[],
                          hardware_ready=False, manual_recovery_permitted=False)
        self.save()

    def save(self):
        try:
            super().save()
        except OSError as exc:
            raise b.UncertainTransport('Cannot persist run evidence; stop without further transport') from exc

    def finish(self, outcome, **data):
        # A journal cannot authorize mode entry or certify a person's presence.
        data.update(manual_recovery_permitted=False, hardware_ready=False, completed_at=time.time())
        return super().finish(outcome, **data)


class Transport(b.AdbRootTransport):
    def __init__(self, directory, journal, action, pin, run):
        super().__init__(directory, journal, 'install' if action == 'install' else 'restore')
        self.action, self.pin, self.run = action, pin, run
        self.session = b.BASE + '/' + canonical_run(run) + '-' + action
        self.vault, self.inbox = self.session + '/vault', self.session + '/inbox'
        self.usb = o.Adb(self.usb_command)
        self.last_root = None
        self.last_command = None

    def command(self, argv, *, script=None, timeout=90):
        result = super().command(argv, script=script, timeout=timeout)
        path = self.directory / f'command-{self.sequence:03}.json'
        self.last_command = path
        self.journal.state['command_receipts'].append(dict(file=path.name, sha256=digest(path.read_bytes())))
        self.journal.save()
        if argv == [sys.executable, str(b.HELPER)]:
            self.last_root = path
        return result

    def usb_command(self, argv, **kwargs):
        # Observer gets bytes, while the inherited audited command logger uses text.
        result = self.command(argv, timeout=12)
        return subprocess.CompletedProcess(argv, result.returncode, result.stdout.encode(), result.stderr.encode())

    def usb_check(self, full=False):
        try:
            row = o.select(self.usb.inventory(), self.pin)
            o.check(row == self.pin['stock'], 'USB enumeration changed; no automatic repin')
            if full:
                o.stock_checks(self.usb, row, self.pin)
            self.journal.event('current_stock_usb_verified', row=row, full_properties=full)
        except (o.Refused, UnicodeError, ValueError, KeyError) as exc:
            raise b.UncertainTransport('USB preflight/transport failed; stop without retry: ' + str(exc)) from exc

    def healthy(self):
        self.usb_check(full=True)
        super().healthy()

    def root(self, body, label):
        self.usb_check()
        try:
            super().root(body, label)
        except b.OperationFailed:
            self.usb_check()
            raise
        self.usb_check()

    def pull(self, label):
        root_record = self.last_root
        data = super().pull(label)
        pull_record = self.last_command
        if label == 'recovery':
            event = self.journal.state['events'][-1]
            self.journal.state['captures'].append(dict(
                run_id=self.run, pin_sha256=o.object_sha(self.pin), at=time.time(),
                bytes=len(data), sha256=digest(data), file=Path(event['path']).name,
                source=b.BLOCK, root_command=root_record.name,
                root_command_sha256=digest(root_record.read_bytes()),
                pull_command=pull_record.name, pull_command_sha256=digest(pull_record.read_bytes()),
                session=self.session))
            self.journal.save()
        return data

    def write(self, kind):
        if kind == 'candidate':
            validate_pin(self.pin, self.run)  # Refuse if staging outlived the fresh pin.
        super().write(kind)


def check_install(run, code_sha):
    path = RUNS / canonical_run(run) / 'install/state.json'
    state = json_file(path)
    require(state.get('mode') == 'EXECUTE' and state.get('run_id') == run and
            state.get('profile') == o.PROFILE and state.get('candidate_sha256') == o.IMAGE_SHA and
            state.get('code_sha256') == code_sha and state.get('profile_sha256') == PROFILE_SHA,
            'Install journal binding mismatch')
    require(state.get('outcome') == 'installed_full_hash_verified' and state.get('cleanup') == 'verified',
            'No clean verified install; uncertain/failed runs need parent assessment, never retry here')
    require(state.get('write_dispatches') == [dict(source='candidate', target=b.BLOCK)],
            'Install already used inverse or has unexpected dispatches')
    require(state.get('pin_sha256') == o.object_sha(state['pin']), 'Install pin changed')
    validate_pin(state['pin'], run, now=state['started_at'])
    return path, state


def prior_restore_guard(run):
    directory = RUNS / run / 'restore'
    if directory.exists():
        state = json_file(directory / 'state.json')
        require(state.get('outcome') in ('restored_full_hash_verified', 'verified_already_restored') and
                state.get('cleanup') == 'verified' and state.get('restore_verified') is True,
                'Prior restore incomplete/uncertain; stop for parent assessment, no follow-up transport')


def run_readback(transport, journal):
    try:
        transport.healthy()
        transport.setup()
        data = transport.read()
        require(digest(data) == b.STOCK_HASH, 'Readback is not exact full stock recovery')
        transport.healthy()
        transport.cleanup()
        transport.healthy()
        return journal.finish('stock_readback_verified', restore_verified=True, cleanup='verified')
    except b.UncertainTransport as exc:
        return journal.finish('transport_uncertain_no_retry', error=str(exc))
    except (b.Refused, b.OperationFailed, b.VerificationFailed, OSError) as exc:
        return journal.finish('readback_unverified_stop', error=str(exc))


def capture_for_finalize(state_path, run, install, observation):
    state = json_file(state_path)
    require(state_path.resolve() in [(RUNS / run / p / 'state.json').resolve() for p in ('restore', 'readback')],
            'Use this run\'s actual restore/readback journal')
    require(state.get('mode') == 'EXECUTE' and state.get('run_id') == run and
            state.get('profile') == o.PROFILE and state.get('candidate_sha256') == o.IMAGE_SHA and
            state.get('profile_sha256') == PROFILE_SHA and state.get('code_sha256') == code_receipt()['sha256'],
            'Reader run/profile/code mismatch')
    require(state.get('install_journal_sha256') == digest((RUNS / run / 'install/state.json').read_bytes()),
            'Install journal changed')
    require(state.get('outcome') in ('restored_full_hash_verified', 'verified_already_restored', 'stock_readback_verified')
            and state.get('restore_verified') is True and state.get('cleanup') == 'verified', 'Reader did not finish cleanly')
    require(state['pin']['stock']['usb'] == install['pin']['stock']['usb'], 'Reader USB topology differs from trial')
    require(state.get('pin_sha256') == o.object_sha(state['pin']), 'Reader pin changed')
    validate_pin(state['pin'], run, now=state['started_at'])
    require(state['started_at'] >= observation['returned_at'], 'Reader started before observed stock return')
    captures = state['captures']
    require(bool(captures), 'No actual partition capture')
    capture = captures[-1]
    require(capture['source'] == b.BLOCK and capture['run_id'] == run and
            capture['pin_sha256'] == state['pin_sha256'] and capture['bytes'] == b.SIZE and
            capture['sha256'] == b.STOCK_HASH and
            state['started_at'] <= capture['at'] <= state['completed_at'] <= time.time(), 'Capture binding/chronology mismatch')
    directory = state_path.parent
    for receipt in state['command_receipts']:
        require(Path(receipt['file']).name == receipt['file'], 'Unsafe command filename')
        require(digest(b.read_bounded(directory / receipt['file'])) == receipt['sha256'], 'Command evidence changed')
    records = {}
    for name in ('root_command', 'pull_command'):
        filename = capture[name]
        require(Path(filename).name == filename, 'Unsafe capture command')
        data = b.read_bounded(directory / filename)
        require(digest(data) == capture[name + '_sha256'], 'Capture command changed')
        records[name] = json.loads(data)
    root, pull = records['root_command'], records['pull_command']
    require(root['status'] == 'returned' and root['argv'] == [sys.executable, str(b.HELPER)], 'No completed pinned reader')
    script = root['stdin']
    expected_read = f"dd if={b.BLOCK} of={capture['session']}/vault/readback.bin bs=512 count={b.SECTORS}"
    require(b.DEVICE_GUARD in script and expected_read in script and
            not re.search(r'dd if=\S+ of=' + re.escape(b.BLOCK), script), 'Not a guarded full-p10 read')
    tokens = re.findall(r'ASUS_RECOVERY_RC_([0-9a-f]{32})=', script)
    require(len(tokens) == 1, 'Reader status token invalid')
    require(b.root_status(subprocess.CompletedProcess(root['argv'], root['exit_status'], root['stdout'], root['stderr']), tokens[0]) == 0,
            'Reader failed')
    filename = capture['file']
    require(Path(filename).name == filename, 'Unsafe capture filename')
    readback = directory / filename
    require(pull['status'] == 'returned' and pull['exit_status'] == 0 and
            pull['argv'] == ['adb', '-s', b.ENDPOINT, 'pull', capture['session'] + '/inbox/readback.bin', str(readback)],
            'Not the journaled Wi-Fi capture')
    require(len(b.read_bounded(readback)) == b.SIZE and digest(b.read_bounded(readback)) == b.STOCK_HASH,
            'Captured bytes changed')
    return readback, state


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=('plan', 'verify-local', 'install', 'restore', 'readback', 'finalize'))
    p.add_argument('--execute', action='store_true')
    p.add_argument('--run-id')
    p.add_argument('--pin', type=Path)
    p.add_argument('--observation', type=Path)
    p.add_argument('--reader-journal', type=Path)
    p.add_argument('--reviewed-profile-sha256')
    p.add_argument('--reviewed-code-sha256')
    p.add_argument('--parent-reviewed', action='store_true')
    p.add_argument('--supervised', action='store_true')
    p.add_argument('--physical-fallback-present', action='store_true')
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    os.umask(0o077)
    journal = None
    try:
        stock, full, local = verify_local()
        if not args.execute:
            print(json.dumps(dict(mode='PLAN_ONLY', action=args.action, **local,
                                  live_gates=['parent review of profile and code digest', 'truthful supervision and nearby physical fallback',
                                              'fresh same-run exact-stock USB pin and fixed authenticated Wi-Fi',
                                              'shared mutation lock; no other writers; no automatic mode entry'],
                                  manual_recovery_permitted=False), indent=2))
            return 0
        require(args.action not in ('plan', 'verify-local'), 'Offline action cannot execute')
        require(args.action != 'install',
                'R2 INSTALL QUARANTINED: exact LK relocates ramdisk to 0x44000000; '
                'the R2 initrd token skips 512 bytes. Use the separately reviewed corrected R3 profile.')
        require(args.parent_reviewed and args.supervised and args.physical_fallback_present,
                'Truthful parent review, current supervision and nearby physical fallback attestations required')
        require(args.reviewed_profile_sha256 == PROFILE_SHA and args.reviewed_code_sha256 == local['code']['sha256'],
                'Parent-reviewed code/profile hashes required')
        run = canonical_run(args.run_id)
        require(args.pin is not None, 'Fresh current stock USB pin required')
        pin = json_file(args.pin)
        validate_pin(pin, run)
        with mutation_lock():
            install_path, install = (None, None) if args.action == 'install' else check_install(run, local['code']['sha256'])
            if install:
                require(pin['stock']['usb'] == install['pin']['stock']['usb'], 'USB topology changed from trial')
            if args.action in ('readback', 'finalize'):
                prior_restore_guard(run)
            observation = None
            if args.action == 'finalize':
                require(args.observation is not None and args.reader_journal is not None,
                        'Observer result and actual reader journal required')
                observation = json_file(args.observation)
                readback, reader = capture_for_finalize(args.reader_journal, run, install, observation)
            directory = reserve(run, args.action)
            journal = Journal(directory, args.action, run, pin, dict(parent_reviewed=True, supervised=True,
                              physical_fallback_present=True, attestation_is_not_physical_proof=True))
            journal.state['local_inputs'] = local['inputs']
            if install:
                journal.state.update(install_journal_sha256=digest(install_path.read_bytes()))
            journal.save()
            transport = Transport(directory, journal, args.action, pin, run)
            if args.action == 'finalize':
                transport.healthy()
                result = o.finalize(transport.usb, install['pin'], run, observation, args.observation.parent, readback)
                result.update(reader_journal=str(args.reader_journal),
                              reader_journal_sha256=digest(args.reader_journal.read_bytes()),
                              install_journal_sha256=digest(install_path.read_bytes()),
                              readback_provenance='Same-run guarded p10 dd plus fixed Wi-Fi pull, linked command journals; host evidence is not hardware attestation',
                              hardware_ready=False)
                b.write_json(directory / 'acceptance.json', result)
                state = journal.finish('diagnostic_and_stock_restoration_accepted', acceptance=result)
            elif args.action == 'readback':
                state = run_readback(transport, journal)
            else:
                state = b.execute(args.action, stock, full if args.action == 'install' else None, transport, journal)
            print(json.dumps(dict(outcome=state['outcome'], evidence=str(directory), hardware_ready=False,
                                  manual_recovery_permitted=False), indent=2))
            return 0 if state['outcome'] in ('installed_full_hash_verified', 'restored_full_hash_verified',
                    'verified_already_restored', 'stock_readback_verified', 'diagnostic_and_stock_restoration_accepted') and state.get('cleanup') != 'unverified' else 2
    except (b.Refused, b.OperationFailed, b.VerificationFailed, b.UncertainTransport, o.Refused,
            OSError, ValueError, TypeError, KeyError) as exc:
        if journal:
            try:
                journal.finish('refused_or_uncertain_stop', error=str(exc))
            except (b.UncertainTransport, OSError):
                pass  # Existing evidence remains; no further target operations.
        print(json.dumps(dict(outcome='REFUSED_OR_UNCERTAIN_STOP', error=str(exc), hardware_ready=False,
                              manual_recovery_permitted=False)), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
