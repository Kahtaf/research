#!/usr/bin/env python3
"""One stock-kernel recovery control and its exact stock inverse. Offline by default."""
from __future__ import annotations

import argparse
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import struct
import subprocess
import sys

SPIKE = Path(__file__).resolve().parents[1]
WORKSPACE = SPIKE.parent
SERIAL = 'DEVICE_SERIAL_REDACTED'
ENDPOINT = 'IP_REDACTED:5555'
TRANSPORT = dict(kind='adb-tcp', endpoint=ENDPOINT, secure_adb='1')
# Same host lock as the original USB writer: neither may run concurrently.
EXECUTE_LOCK = WORKSPACE / '2026-11-06-asus-recovery-control-transport/evidence/execute.lock'
FINGERPRINT = 'asus/WW_P00A/P00A_2:7.0/NRD90M/WW_P00A-V5.3.20-20180809:user/release-keys'
BLOCK = '/dev/block/mmcblk0p10'
ALIAS = '/dev/block/platform/mtk-msdc.0/11230000.MSDC0/by-name/recovery'
SIZE = 16740352
SECTORS = 32696
STOCK_HASH = '902b2f06a01cca574b4aa374e67c4e7f8f0ed53f6e6a55017b6d96351f0f1f20'
KERNEL_HASH = 'b0e5d48bf2889b418dda0fc867f70e42e27a0aeb0a0a3d37539d9a7435430880'
HELPER = WORKSPACE / '2026-11-06-asus-wifi-device-access/scripts/root_shell_wifi.py'
HELPER_HASH = '684bbe346488dfd0e7dfce741b7547021f019d3749235e6208eb1c9766395f34'
ROOT_BINARY = WORKSPACE / '2026-11-05-asus-root-hardware-validation/sources/mtk-su-mirror-b'
ROOT_BINARY_HASH = '328632e853ff6427af9f35cb83a91d9e960f35d01188ee66d46ae9c7ce7c7827'
BACKUPS = tuple(WORKSPACE / '2026-11-05-asus-boot-access-audit/artifacts/device-backup' / label / 'recovery.bin'
                for label in ('initial', 'verify'))
BASE = '/data/local/tmp/asus-recovery-control-wifi'
TARGET = dict(serial=SERIAL, product='P00A_2', sdk='24', fingerprint=FINGERPRINT,
              block=BLOCK, by_name=ALIAS, bytes=SIZE, sectors=SECTORS,
              start_sector=160184, logical_sector_bytes=512, major_minor='179:10')
PROFILE = 'stock-kernel-changed-ramdisk-control-v1'


class Refused(Exception):
    """A guard failed before an authorized write."""


class OperationFailed(Exception):
    """Root operation returned a recorded nonzero status; transport still answered."""


class UncertainTransport(Exception):
    """No reliable completion/health evidence. Never retry automatically."""


class VerificationFailed(Exception):
    pass


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise Refused(message)


def write_json(path, data):
    temporary = path.with_suffix('.pending')
    temporary.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n')
    temporary.replace(path)


def read_bounded(path, maximum=SIZE):
    require(path.is_file() and not path.is_symlink(), f'Not a regular nonsymlink file: {path}')
    with path.open('rb') as stream:
        data = stream.read(maximum + 1)
    require(len(data) <= maximum, f'Input exceeds {maximum} bytes: {path}')
    return data


def local_inputs():
    records = []
    stock = None
    for path in BACKUPS:
        data = read_bounded(path)
        require(len(data) == SIZE and sha(data) == STOCK_HASH, f'Stock backup mismatch: {path}')
        records.append(dict(path=str(path), bytes=len(data), sha256=sha(data)))
        stock = data
    for path, expected in ((HELPER, HELPER_HASH), (ROOT_BINARY, ROOT_BINARY_HASH)):
        data = read_bounded(path)
        require(sha(data) == expected, f'Pinned root dependency changed: {path}')
        records.append(dict(path=str(path), bytes=len(data), sha256=sha(data)))
    return stock, records


def unpack_image(data):
    require(len(data) >= 2048 and data[:8] == b'ANDROID!', 'Expected legacy Android boot image')
    values = struct.unpack_from('<10I', data, 8)
    kernel_size, _, ramdisk_size, _, second_size, _, _, page, dt_size, _ = values
    require(page == 2048 and second_size == 0 and dt_size == 0, 'Unsupported header/layout')
    require(kernel_size >= 512 and ramdisk_size >= 512, 'Missing wrapped kernel or ramdisk')
    align = lambda n: (n + page - 1) // page * page
    ramdisk_offset = page + align(kernel_size)
    end = ramdisk_offset + align(ramdisk_size)
    require(end <= len(data) <= SIZE, 'Truncated or oversized image')
    kernel = data[page:page + kernel_size]
    ramdisk = data[ramdisk_offset:ramdisk_offset + ramdisk_size]
    for payload, name in ((kernel, b'KERNEL'), (ramdisk, b'RECOVERY')):
        require(payload[:4] == bytes.fromhex('88168858'), 'Missing MTK wrapper')
        require(struct.unpack_from('<I', payload, 4)[0] == len(payload) - 512,
                'MTK wrapper length mismatch')
        require(payload[8:40].rstrip(b'\0') == name, 'MTK wrapper name mismatch')
    return dict(header=values, kernel=kernel, ramdisk=ramdisk, end=end)


def exact_keys(value, keys, label):
    require(type(value) is dict and set(value) == set(keys), f'Unexpected {label} fields')


def validate_candidate(path, reviewed_hash, stock):
    raw = read_bounded(path, 65536)
    require(re.fullmatch('[0-9a-f]{64}', reviewed_hash or '') is not None,
            'Supply the independently reviewed manifest SHA256')
    require(sha(raw) == reviewed_hash, 'Reviewed manifest hash mismatch')
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, f'Duplicate manifest key: {key}')
            result[key] = value
        return result
    manifest = json.loads(raw, object_pairs_hook=unique)
    exact_keys(manifest, ('schema_version', 'profile', 'target', 'candidate', 'padding', 'review'), 'manifest')
    require(type(manifest['schema_version']) is int and manifest['schema_version'] == 1,
            'Unsupported schema')
    require(manifest['profile'] == PROFILE and manifest['target'] == TARGET, 'Wrong profile or target')
    c, p, review = (manifest[k] for k in ('candidate', 'padding', 'review'))
    exact_keys(c, ('path', 'bytes', 'sha256', 'wrapped_kernel_sha256', 'header_page_sha256'), 'candidate')
    exact_keys(p, ('kind', 'byte', 'full_partition_sha256'), 'padding')
    exact_keys(review, ('approved', 'reviewer', 'reference', 'marker', 'bounded_return_seconds',
                        'ram_only_no_persistent_mounts_or_writes', 'manual_recovery_and_normal_boot'), 'review')
    require(review['approved'] is True and review['ram_only_no_persistent_mounts_or_writes'] is True
            and review['manual_recovery_and_normal_boot'] is True, 'Review attestations absent')
    for key in ('reviewer', 'reference', 'marker'):
        require(type(review[key]) is str and 0 < len(review[key].strip()) <= 1000, f'Missing {key}')
    require(type(review['bounded_return_seconds']) is int and 1 <= review['bounded_return_seconds'] <= 600,
            'Return deadline must be 1..600 seconds')
    require(type(c['path']) is str and c['path'] and not Path(c['path']).is_absolute(),
            'Candidate path must be local and relative to manifest')
    candidate_path = path.parent / c['path']
    image = read_bounded(candidate_path)
    require(type(c['bytes']) is int and len(image) == c['bytes'] and sha(image) == c['sha256'],
            'Candidate size/hash mismatch')
    require(p['kind'] == 'constant-byte' and type(p['byte']) is int and 0 <= p['byte'] <= 255,
            'Padding must specify one reviewed byte, 0..255')
    parsed, original = unpack_image(image), unpack_image(stock)
    require(len(image) == parsed['end'], 'Candidate must end at the aligned ramdisk boundary (no trailer)')
    require(parsed['kernel'] == original['kernel'] and sha(parsed['kernel']) == KERNEL_HASH
            and c['wrapped_kernel_sha256'] == KERNEL_HASH, 'First control must keep the exact stock kernel/DTB/wrapper')
    require(parsed['ramdisk'] != original['ramdisk'], 'First control needs a changed ramdisk')
    require(all(parsed['header'][i] == original['header'][i] for i in (0, 1, 3, 4, 5, 6, 7, 8, 9)),
            'Stock header addresses/page/legacy fields changed')
    require(sha(image[:2048]) == c['header_page_sha256'], 'Header page hash mismatch')
    full = image + bytes([p['byte']]) * (SIZE - len(image))
    require(sha(full) == p['full_partition_sha256'] and sha(full) != STOCK_HASH, 'Full padded hash mismatch')
    return full, dict(manifest_path=str(path.resolve()), manifest_sha256=sha(raw), manifest=manifest,
                      bounded_bytes=len(image), full_bytes=len(full), full_sha256=sha(full))


# Android7 stat lacks %t/%T. Numeric ls exposes st_rdev on this exact stock
# build; retain the independent sysfs major/minor and canonical-node checks.
NODE_RDEV_GUARD = f'''asus_node_listing=$(ls -ln {BLOCK})
set -- $asus_node_listing
[ "$#" -eq 9 ]
[ "$5" = 179, ]
[ "$6" = 10 ]
[ "$9" = {BLOCK} ]'''

# These guards precede every root read/write; no caller-supplied shell fragments.
DEVICE_GUARD = f'''[ "$(id -u)" = 0 ]
[ "$(getprop ro.serialno)" = '{SERIAL}' ]
[ "$(getprop ro.product.device)" = P00A_2 ]
[ "$(getprop ro.build.version.sdk)" = 24 ]
[ "$(getprop ro.build.fingerprint)" = '{FINGERPRINT}' ]
[ "$(getprop sys.boot_completed)" = 1 ]
[ "$(getprop ro.adb.secure)" = 1 ]
[ -b {BLOCK} ]
[ "$(readlink -f {BLOCK})" = {BLOCK} ]
[ "$(readlink -f {ALIAS})" = {BLOCK} ]
[ "$(cat /sys/class/block/mmcblk0p10/partition)" = 10 ]
[ "$(cat /sys/class/block/mmcblk0p10/start)" = 160184 ]
[ "$(cat /sys/class/block/mmcblk0p10/size)" = {SECTORS} ]
[ "$(cat /sys/class/block/mmcblk0p10/dev)" = 179:10 ]
{NODE_RDEV_GUARD}
[ "$(cat /sys/class/block/mmcblk0/queue/logical_block_size)" = 512 ]'''


def directory_guard(path, owner_mode):
    return f'''[ ! -L {path} ]
[ -d {path} ]
[ "$(stat -c '%u:%a' {path})" = {owner_mode} ]'''


def root_envelope(body, token):
    require(re.fullmatch('[0-9a-f]{32}', token) is not None, 'Internal status token invalid')
    return f'''(
set -eu
umask 077
{DEVICE_GUARD}
{body}
)
asus_operation_rc=$?
printf '\\nASUS_RECOVERY_RC_{token}=%s\\n' "$asus_operation_rc"
# Status is carried in the mandatory record; helper status proves its own completion.
exit 0
'''


def root_status(result, token):
    matches = re.findall(r'^ASUS_RECOVERY_RC_' + token + r'=(\d{1,3})\r?$', result.stdout, re.M)
    if len(matches) != 1:
        raise UncertainTransport('Missing/ambiguous root completion status; no automatic retry')
    status = int(matches[0])
    if not 0 <= status <= 255 or result.returncode != 0:
        raise UncertainTransport('Root status disagrees with helper/SELinux completion; no automatic retry')
    return status


class Journal:
    def __init__(self, directory, action, mode):
        self.directory = directory
        self.state = dict(action=action, mode=mode, target=TARGET, outcome='preparing',
                          transport=TRANSPORT, events=[], write_dispatches=[], restore_verified=False,
                          manual_recovery_permitted=False)
        self.save()

    def save(self):
        write_json(self.directory / 'state.json', self.state)

    def event(self, kind, **data):
        self.state['events'].append(dict(at=dt.datetime.now(dt.timezone.utc).isoformat(), kind=kind, **data))
        self.save()

    def finish(self, outcome, **data):
        self.state.update(outcome=outcome, **data)
        self.save()
        return self.state


class AdbRootTransport:
    """Only constructed by main after --execute and all offline guards pass."""
    def __init__(self, directory, journal, action):
        require(action in ('install', 'restore'), 'Unsupported action')
        self.directory, self.journal = directory, journal
        self.session = BASE + '/' + action
        self.vault, self.inbox = self.session + '/vault', self.session + '/inbox'
        self.sequence = 0
        self.stage_created = False

    def command(self, argv, *, script=None, timeout=90):
        self.sequence += 1
        path = self.directory / f'command-{self.sequence:03}.json'
        record = dict(argv=argv, stdin=script, status='dispatched')
        write_json(path, record)
        try:
            result = subprocess.run(argv, input=script, text=True, capture_output=True, timeout=timeout)
        except (subprocess.TimeoutExpired, OSError) as exc:
            record.update(status='uncertain', error=str(exc))
            try:
                write_json(path, record)
            except OSError:
                pass
            raise UncertainTransport(f'Command did not complete; see {path.name}') from exc
        record.update(status='returned', exit_status=result.returncode, stdout=result.stdout, stderr=result.stderr)
        try:
            write_json(path, record)
        except OSError as exc:
            raise UncertainTransport('Cannot persist command completion; no automatic retry') from exc
        return result

    def adb(self, args, timeout=60):
        result = self.command(['adb', '-s', ENDPOINT, *args], timeout=timeout)
        if result.returncode != 0:
            raise UncertainTransport(f'ADB command returned {result.returncode}; no automatic retry')
        return result.stdout.strip()

    def healthy(self):
        require(self.adb(['get-serialno']) == ENDPOINT, 'Wrong ADB transport endpoint')
        props = [('ro.serialno', SERIAL), ('ro.product.device', 'P00A_2'),
                 ('ro.build.version.sdk', '24'), ('ro.build.fingerprint', FINGERPRINT),
                 ('sys.boot_completed', '1'), ('ro.adb.secure', '1')]
        for prop, expected in props:
            require(self.adb(['shell', 'getprop', prop]) == expected, f'Wrong/unhealthy {prop}')
        require(self.adb(['shell', 'getenforce']) == 'Enforcing', 'Stock Android not Enforcing')
        self.journal.event('stock_android_health_verified')

    def root(self, body, label):
        # Recheck locally before EVERY helper invocation; never replace its guards.
        require(sha(read_bounded(HELPER)) == HELPER_HASH, 'Root helper changed')
        require(sha(read_bounded(ROOT_BINARY)) == ROOT_BINARY_HASH, 'Root binary changed')
        token = secrets.token_hex(16)
        result = self.command([sys.executable, str(HELPER)], script=root_envelope(body, token), timeout=95)
        status = root_status(result, token)
        self.journal.event('root_status', operation=label, exit_status=status, helper_exit_status=result.returncode)
        if status:
            raise OperationFailed(f'{label}: root operation exit status {status}')

    def stage_guard(self):
        return '\n'.join(directory_guard(p, m) for p, m in
                         ((BASE, '0:711'), (self.session, '0:711'),
                          (self.vault, '0:700'), (self.inbox, '2000:700')))

    def setup(self):
        self.root(f'''if [ ! -e {BASE} ] && [ ! -L {BASE} ]; then
    mkdir {BASE}
    chmod 711 {BASE}
fi
{directory_guard(BASE, '0:711')}
[ ! -e {self.session} ]
[ ! -L {self.session} ]
mkdir {self.session}
chmod 711 {self.session}
mkdir {self.vault} {self.inbox}
chmod 700 {self.vault} {self.inbox}
chown 2000:2000 {self.inbox}
{self.stage_guard()}''', 'create_private_staging')
        self.stage_created = True

    def export(self, source):
        # Source is selected only from fixed internal vault filenames.
        return f'''rm -f {self.inbox}/readback.bin
cp {source} {self.inbox}/readback.bin
chmod 600 {self.inbox}/readback.bin
chown 2000:2000 {self.inbox}/readback.bin'''

    def pull(self, label):
        path = self.directory / f'{self.sequence:03}-{label}.bin'
        self.adb(['pull', self.inbox + '/readback.bin', str(path)])
        data = read_bounded(path)
        if len(data) != SIZE:
            raise VerificationFailed(f'{label}: incomplete full-partition readback ({len(data)})')
        self.journal.event('full_readback', label=label, bytes=len(data), sha256=sha(data), path=str(path))
        return data

    def stage(self, kind, data):
        require(kind in ('stock', 'candidate') and len(data) == SIZE, 'Invalid staging input')
        path = self.directory / f'{kind}-full.bin'
        path.write_bytes(data)
        self.adb(['push', str(path), self.inbox + '/input.bin'])
        dest = self.vault + '/' + kind + '.bin'
        self.root(f'''{self.stage_guard()}
[ ! -L {self.inbox}/input.bin ]
[ -f {self.inbox}/input.bin ]
[ "$(wc -c < {self.inbox}/input.bin)" -eq {SIZE} ]
[ ! -e {dest} ]
[ ! -L {dest} ]
cp {self.inbox}/input.bin {dest}
chmod 400 {dest}
rm {self.inbox}/input.bin
{self.export(dest)}''', 'stage_' + kind)
        if self.pull('staged-' + kind) != data:
            raise VerificationFailed('Staged ' + kind + ' differs from reviewed bytes')

    def read(self):
        self.root(f'''{self.stage_guard()}
dd if={BLOCK} of={self.vault}/readback.bin bs=512 count={SECTORS}
[ "$(wc -c < {self.vault}/readback.bin)" -eq {SIZE} ]
{self.export(self.vault + '/readback.bin')}''', 'read_full_recovery')
        return self.pull('recovery')

    def write(self, kind):
        require(kind in ('stock', 'candidate'), 'Invalid write source')
        source = self.vault + '/' + kind + '.bin'
        self.root(f'''{self.stage_guard()}
[ ! -L {source} ]
[ -f {source} ]
[ "$(stat -c '%u:%a' {source})" = 0:400 ]
[ "$(wc -c < {source})" -eq {SIZE} ]
dd if={source} of={BLOCK} bs=512 count={SECTORS}
sync''', 'write_' + kind)

    def cleanup(self):
        if not self.stage_created:
            return
        self.root(f'''{self.stage_guard()}
rm -f {self.vault}/stock.bin {self.vault}/candidate.bin {self.vault}/readback.bin
rm -f {self.inbox}/input.bin {self.inbox}/readback.bin
rmdir {self.vault} {self.inbox}
rmdir {self.session}''', 'cleanup_private_staging')
        self.stage_created = False


def execute(action, stock, candidate, transport, journal):
    """At most one candidate attempt and one stock inverse; unknown transport stops."""
    write_started = False

    def dispatch(kind):
        nonlocal write_started
        write_started = True
        journal.state['write_dispatches'].append(dict(source=kind, target=BLOCK))
        journal.event('write_dispatched', source=kind, target=BLOCK)
        transport.write(kind)

    def verify_stock():
        data = transport.read()
        if len(data) != SIZE or sha(data) != STOCK_HASH:
            raise VerificationFailed('Exact full stock readback does not match')
        transport.healthy()
        journal.event('stock_inverse_verified', sha256=STOCK_HASH, bytes=SIZE)

    try:
        transport.healthy()
        transport.setup()
        transport.stage('stock', stock)
        if action == 'install':
            transport.stage('candidate', candidate)
        before = transport.read()
        require(len(before) == SIZE, 'Current recovery readback size mismatch')
        if action == 'install':
            require(sha(before) == STOCK_HASH, 'Install requires current recovery to equal exact stock')
            transport.healthy()
            dispatch('candidate')
            after = transport.read()
            if len(after) != SIZE or sha(after) != sha(candidate):
                raise VerificationFailed('Full candidate readback mismatch')
            transport.healthy()
            result = 'installed_full_hash_verified'
        elif sha(before) == STOCK_HASH:
            transport.healthy()
            result = 'verified_already_restored'
        else:
            transport.healthy()
            dispatch('stock')
            verify_stock()
            result = 'restored_full_hash_verified'
    except UncertainTransport as exc:
        return journal.finish('transport_uncertain_no_retry', error=str(exc),
                              partition_may_be_modified=write_started,
                              next_action='No automatic commands. Parent must assess transport and manually return to stock Android.')
    except (Refused, OperationFailed, VerificationFailed, OSError) as exc:
        journal.event('operation_failed', error=str(exc), partition_may_be_modified=write_started)
        if write_started and action == 'install':
            try:
                # Only a fresh, fully checked stock Android session permits the inverse.
                transport.healthy()
                try:
                    current = transport.read()
                except (OperationFailed, VerificationFailed, OSError) as read_error:
                    # A completed read failure is not transport loss. The fixed stock
                    # inverse is still useful; its own geometry guards run again.
                    journal.event('inverse_preread_failed', error=str(read_error))
                    transport.healthy()
                    current = None
                if current is not None and len(current) == SIZE and sha(current) == STOCK_HASH:
                    transport.healthy()
                    result = 'install_failed_verified_already_restored'
                else:
                    dispatch('stock')
                    verify_stock()
                    result = 'install_failed_stock_inverse_verified'
            except (Refused, OperationFailed, VerificationFailed, UncertainTransport, OSError) as inverse_error:
                return journal.finish('inverse_unverified_stop', error=str(exc), inverse_error=str(inverse_error),
                                      partition_may_be_modified=True,
                                      next_action='No retries or reboot. Parent must assess and regain healthy stock Android.')
        else:
            return journal.finish('restore_unverified_stop' if write_started else 'refused_before_write',
                                  error=str(exc), partition_may_be_modified=write_started)
    # Cleanup is independent evidence, never a replacement for the operation status.
    restored = result != 'installed_full_hash_verified'
    journal.finish(result, restore_verified=restored,
                   manual_recovery_permitted=False, cleanup='pending')
    try:
        transport.cleanup()
        transport.healthy()
    except (Refused, OperationFailed, VerificationFailed, UncertainTransport, OSError) as exc:
        return journal.finish(result, cleanup='unverified', cleanup_error=str(exc),
                              manual_recovery_permitted=False,
                              next_action='Parent must resolve cleanup/health before any manual Recovery selection.')
    return journal.finish(result, cleanup='verified',
                          manual_recovery_permitted=(result == 'installed_full_hash_verified'),
                          next_action='Parent decides manual Recovery/Normal Boot; this tool never reboots or selects a boot mode.')


def new_run():
    parent = SPIKE / 'evidence/runs'
    parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    path = parent / (dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ-') + secrets.token_hex(4))
    path.mkdir(mode=0o700)
    return path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('install', 'restore', 'verify-local'))
    parser.add_argument('--manifest', type=Path)
    parser.add_argument('--reviewed-manifest-sha256')
    parser.add_argument('--execute', action='store_true', help='Explicit device operations; absent means offline PLAN ONLY')
    parser.add_argument('--supervised', action='store_true', help='Parent attests user presence and manual boot/return plan')
    args = parser.parse_args(argv)
    os.umask(0o077)
    out = new_run()
    journal = Journal(out, args.action, 'EXECUTE' if args.execute else 'PLAN_ONLY')
    try:
        require(not (args.execute and args.action == 'verify-local'), 'verify-local cannot execute')
        require(not args.execute or args.supervised, 'Execution requires explicit --supervised attestation')
        require(args.action == 'install' or (args.manifest is None and args.reviewed_manifest_sha256 is None),
                'Restore uses only the two fixed stock backups, never a candidate manifest')
        stock, records = local_inputs()
        journal.state['local_inputs'] = records
        candidate, reviewed = None, None
        if args.action == 'install':
            require(args.manifest is not None, 'Install requires a reviewed candidate manifest')
            candidate, reviewed = validate_candidate(args.manifest, args.reviewed_manifest_sha256, stock)
            journal.state['candidate_review'] = reviewed
        journal.save()
        plan = dict(mode='PLAN_ONLY' if not args.execute else 'EXECUTE', target=TARGET, transport=TRANSPORT,
                    stock_sha256=STOCK_HASH, candidate=reviewed,
                    steps=['Verify local immutable backups, root helper and root binary',
                           'Verify exact serial, stock OS, boot completion and Enforcing',
                           'Guard recovery alias/node/geometry before every privileged operation',
                           'Create fixed private staging; verify full staged bytes via host readback',
                           'Read full current recovery; install requires exact stock hash',
                           'Write only mmcblk0p10; verify complete readback before manual Recovery',
                           'On known install failure with healthy Android: one exact stock inverse and full verification',
                           'On transport uncertainty: stop without retry, cleanup or reboot',
                           'Restore already-stock: verified_already_restored, no block write'],
                    constraints=['No automatic reboot, boot-mode selection, BCB/para or other partition writes',
                                 'No runtime acceptance/restore claim from an offline plan',
                                 'No concurrent recovery writer or external partition mutation during a session'])
        write_json(out / 'plan.json', plan)
        if not args.execute:
            state = journal.finish('local_inputs_verified' if args.action == 'verify-local' else 'plan_only_validated',
                                   device_contacted=False)
        else:
            with EXECUTE_LOCK.open('a') as lock:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                journal.event('execute_authorized', supervised=True)
                state = execute(args.action, stock, candidate, AdbRootTransport(out, journal, args.action), journal)
        print(json.dumps(dict(outcome=state['outcome'], evidence=str(out),
                              manual_recovery_permitted=state['manual_recovery_permitted']), indent=2))
        success = state['outcome'] in ('plan_only_validated', 'local_inputs_verified',
                                      'installed_full_hash_verified', 'restored_full_hash_verified', 'verified_already_restored')
        return 0 if success and state.get('cleanup') != 'unverified' else 2
    except (Refused, ValueError, KeyError, TypeError, OSError) as exc:
        journal.finish('refused', error=str(exc))
        print(json.dumps(dict(outcome='refused', error=str(exc), evidence=str(out))), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
