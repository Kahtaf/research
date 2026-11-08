#!/usr/bin/env python3
"""Narrow read-only macOS observer. Default invocation does not contact devices."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import plistlib
import re
import stat
import struct
import subprocess
import sys
import time

BASE = Path(__file__).resolve().parents[1]
CONTRACT = json.loads((BASE / 'evidence/host-acceptance.json').read_text())
SERIAL = CONTRACT['usb_serial']


class Refused(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise Refused(message)


def walk(node):
    if isinstance(node, list):
        for child in node:
            yield from walk(child)
    elif isinstance(node, dict):
        yield node
        yield from walk(node.get('IORegistryEntryChildren', []))


def devices(tree):
    # Serial alone is not enough: require a USB device class and stable registry ID.
    return [n for n in walk(tree)
            if n.get('USB Serial Number') == SERIAL
            and n.get('IOObjectClass') in ('IOUSBHostDevice', 'IOUSBDevice')]


def select_media(tree):
    matches = devices(tree)
    require(len(matches) == 1, 'Expected one USB device with exact public serial')
    device = matches[0]
    interfaces = [n for n in walk(device) if 'bInterfaceClass' in n and
                  n.get('IOObjectClass') not in ('IOUSBMassStorageInterfaceNub', 'IOUSBMassStorageDriverNub')]
    require(len(interfaces) == 1, 'Expected exactly one USB interface')
    interface = interfaces[0]
    require(interface.get('IOObjectClass') in ('IOUSBHostInterface', 'IOUSBInterface'),
            'USB interface must be an actual interface object')
    require((interface.get('bInterfaceClass'), interface.get('bInterfaceSubClass'),
             interface.get('bInterfaceProtocol')) == (8, 6, 80),
            'USB interface must be mass storage / SCSI / bulk-only')
    media = [n for n in walk(interface)
             if n.get('IOObjectClass') == 'IOMedia' and n.get('Whole') is True]
    require(len(media) == 1, 'Expected exactly one whole IOMedia below that interface')
    medium = media[0]
    require(medium.get('Size') == 65536, 'IOMedia capacity is not exactly 65536 bytes')
    require(medium.get('Writable') is False, 'IOMedia does not explicitly report media write protection')
    disk = medium.get('BSD Name', '')
    require(re.fullmatch(r'disk[0-9]+', disk) is not None, 'Invalid whole BSD disk identity')
    require(type(device.get('IORegistryEntryID')) is int and
            type(medium.get('IORegistryEntryID')) is int, 'Missing registry identity')
    return {'disk': disk, 'device_registry_id': device['IORegistryEntryID'],
            'media_registry_id': medium['IORegistryEntryID'], 'media_readonly': True}


def verify_disk(info, identity):
    disk = identity['disk']
    require(info.get('DeviceIdentifier') == disk and info.get('DeviceNode') == '/dev/' + disk,
            'diskutil identity mismatch')
    require(info.get('Whole') is True, 'diskutil does not report a whole device')
    require(info.get('TotalSize') == 65536, 'diskutil capacity mismatch')
    # IOMedia Writable=false is the required media-level fact. Never substitute
    # filesystem read-only flags for it; reject any contradictory diskutil fact.
    for key in ('MediaReadOnly', 'ReadOnlyMedia'):
        if key in info:
            require(info[key] is True, 'diskutil contradicts media write protection')
    if 'Writable' in info:
        require(info['Writable'] is False, 'diskutil reports writable access')
    return {'mount_point': info.get('MountPoint'),
            'volume_readonly': info.get('VolumeReadOnly', info.get('ReadOnlyVolume')),
            'diskutil_writable': info.get('Writable')}


def parse_fat(raw):
    require(len(raw) == 65536, 'Raw media must be exactly 65536 bytes')
    u16 = lambda offset: struct.unpack_from('<H', raw, offset)[0]
    require(raw[510:512] == b'\x55\xaa', 'Missing boot signature')
    require((u16(11), raw[13], u16(14), raw[16], u16(17), u16(19), raw[21], u16(22))
            == (512, 1, 1, 2, 32, 128, 248, 1), 'Unexpected FAT12 geometry')
    require(raw[28:36] == bytes(8), 'Unexpected hidden/large sector fields')
    require(raw[43:54] == b'RAMPROBE   ' and raw[54:62] == b'FAT12   ', 'Wrong FAT label/type')
    fat = raw[512:1024]
    require(fat == raw[1024:1536] and fat[:3] == b'\xf8\xff\xff', 'FAT copies or reserved entries differ')
    root = raw[1536:2560]
    require(root[:11] == b'RAMPROBE   ' and root[11] == 8, 'Missing root volume label')
    entry = root[32:64]
    require(entry[:11] == b'REPORT  TXT' and entry[11] == 1, 'Missing sole read-only REPORT.TXT')
    require(not any(root[64:]), 'Extra root entries, deleted entries, or metadata present')
    require(struct.unpack_from('<H', entry, 20)[0] == 0 and
            struct.unpack_from('<H', entry, 26)[0] == 2, 'Unexpected report start cluster')
    size = struct.unpack_from('<I', entry, 28)[0]
    require(0 < size <= 1024, 'Report size outside production bound')
    count = (size + 511) // 512
    expected_fat = bytearray(512)
    expected_fat[:3] = b'\xf8\xff\xff'
    for cluster in range(2, 2 + count):
        value = cluster + 1 if cluster < 1 + count else 0xfff
        offset = cluster + cluster // 2
        if cluster & 1:
            expected_fat[offset] |= (value << 4) & 255
            expected_fat[offset + 1] = value >> 4
        else:
            expected_fat[offset] = value & 255
            expected_fat[offset + 1] |= value >> 8
    require(fat == bytes(expected_fat), 'Unexpected allocation chain or extra allocations')
    require(not any(raw[2560 + size:]), 'Unexpected data outside report')
    report = raw[2560:2560 + size]
    return parse_report(report), report


def parse_report(report):
    require(0 < len(report) <= 1024, 'Report size outside production bound')
    try:
        lines = report.decode('ascii').splitlines(keepends=True)
    except UnicodeError as exc:
        raise Refused('Report is not ASCII') from exc
    fields = {}
    require(len(lines) == 7, 'Report must have exactly seven fields')
    for line in lines:
        require(line.endswith('\n') and '\r' not in line and '=' in line, 'Malformed report line')
        key, value = line[:-1].split('=', 1)
        require(key not in fields, 'Duplicate report field')
        fields[key] = value
    require(fields == CONTRACT['report_exact_fields'], 'Report fields differ from frozen contract')
    return fields


def validate_mountpoint(info, identity):
    state = verify_disk(info, identity)
    mountpoint = info.get('MountPoint')
    require(isinstance(mountpoint, str) and mountpoint.startswith('/Volumes/'),
            'Exact device must be mounted beneath /Volumes')
    components = mountpoint.split('/')[1:]
    require(all(component not in ('', '.', '..') for component in components),
            'Unsafe mountpoint components')
    for key in ('VolumeReadOnly', 'ReadOnlyVolume'):
        if key in info:
            require(info[key] is True, 'diskutil contradicts read-only volume')
    return mountpoint, state


def read_volume_report(mountpoint):
    require(isinstance(mountpoint, str) and mountpoint.startswith('/Volumes/'),
            'Volume reader requires /Volumes mountpoint')
    components = mountpoint.split('/')[1:]
    require(all(part not in ('', '.', '..') for part in components), 'Unsafe mountpoint components')
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_DIRECTORY | os.O_CLOEXEC
    root = os.open('/', flags)
    reportfd = None
    try:
        parent_device = None
        for component in components:
            parent_device = os.fstat(root).st_dev
            child = os.open(component, flags, dir_fd=root)
            os.close(root)
            root = child
        rootstat = os.fstat(root)
        require(stat.S_ISDIR(rootstat.st_mode) and rootstat.st_dev != parent_device,
                'Mountpoint is not a distinct mounted filesystem')
        fs = os.fstatvfs(root)
        require(bool(fs.f_flag & os.ST_RDONLY), 'Actual mounted filesystem is not read-only')
        reportfd = os.open('REPORT.TXT', os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=root)
        before = os.fstat(reportfd)
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and
                0 < before.st_size <= 1024 and before.st_dev == rootstat.st_dev,
                'REPORT.TXT must be a bounded single-link regular file on the exact mounted filesystem')
        chunks = []
        left = before.st_size
        while left:
            block = os.read(reportfd, left)
            require(bool(block), 'Short REPORT.TXT read')
            chunks.append(block)
            left -= len(block)
        require(not os.read(reportfd, 1), 'REPORT.TXT grew during read')
        after = os.fstat(reportfd)
        require((before.st_dev, before.st_ino, before.st_size, before.st_nlink) ==
                (after.st_dev, after.st_ino, after.st_size, after.st_nlink) and
                bool(os.fstatvfs(root).f_flag & os.ST_RDONLY), 'Report or mount state changed during read')
        report = b''.join(chunks)
        parse_report(report)
        return {'report_text': report.decode('ascii'), 'mountpoint': mountpoint,
                'root_st_dev': rootstat.st_dev, 'report_st_dev': before.st_dev,
                'report_st_ino': before.st_ino, 'report_size': before.st_size,
                'filesystem_flags': fs.f_flag, 'filesystem_readonly': True}
    finally:
        if reportfd is not None:
            os.close(reportfd)
        os.close(root)


def remaining(deadline):
    value = deadline - time.monotonic()
    require(value > 0, 'Host observation deadline elapsed; use parent physical fallback')
    return value


def command(args, deadline, limit=64 * 1024 * 1024, record_path=None):
    result = subprocess.run(args, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, timeout=remaining(deadline), check=False)
    if record_path is not None:
        write_private(record_path, (json.dumps({'args': args, 'returncode': result.returncode,
                      'stdout': result.stdout.decode('utf-8', 'replace'),
                      'stderr': result.stderr.decode('utf-8', 'replace')}, indent=2) + '\n').encode())
    require(result.returncode == 0, 'Host command failed: ' + args[0])
    require(len(result.stdout) <= limit, 'Read-only command output exceeds bound')
    return result.stdout


def write_private(path, data):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        os.fchmod(stream.fileno(), 0o600)
        stream.write(data)


def snapshot(output, name, deadline):
    raw = command(['/usr/sbin/ioreg', '-a', '-l', '-w', '0', '-p', 'IOService'], deadline)
    write_private(output / (name + '.plist'), raw)
    return plistlib.loads(raw)


def host_boot_fingerprint(deadline):
    boot = command(['/usr/sbin/sysctl', '-n', 'kern.boottime'], deadline, 4096)
    require(boot.strip(), 'Missing host boot epoch')
    return hashlib.sha256(os.uname().nodename.encode() + b'\x00' + boot).hexdigest()


def baseline_only(output):
    require(sys.platform == 'darwin', '--baseline-only requires macOS')
    require(not output.exists(), 'Evidence directory must not already exist')
    output.mkdir(parents=True, mode=0o700)
    deadline = time.monotonic() + 15
    tree = snapshot(output, 'baseline-ioreg', deadline)
    require(not any(n.get('USB Serial Number') == SERIAL for n in walk(tree)),
            'Serial already present; cannot issue a fresh baseline receipt')
    receipt = {'kind': 'ABSENT_SERIAL_BASELINE_ONLY', 'serial': SERIAL,
               'snapshot': 'baseline-ioreg.plist',
               'snapshot_sha256': hashlib.sha256((output / 'baseline-ioreg.plist').read_bytes()).hexdigest(),
               'host_boot_fingerprint': host_boot_fingerprint(deadline),
               'created_monotonic': time.monotonic(), 'expires_after_seconds': 180}
    path = output / 'baseline-receipt.json'
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'w') as stream:
        json.dump(receipt, stream, indent=2)
        stream.write('\n')
    print('BASELINE_ONLY: serial absent; no positive discriminator. Single-use receipt: ' + str(path))
    return 0


def consume_baseline(path, output, deadline):
    require(path.name == 'baseline-receipt.json', 'Expected exact baseline receipt filename')
    consumed = path.with_name('baseline-receipt.consumed.json')
    require(not consumed.exists(), 'Baseline receipt was already consumed')
    original = os.lstat(path)
    require(stat.S_ISREG(original.st_mode) and original.st_uid == os.getuid() and
            stat.S_IMODE(original.st_mode) == 0o600 and original.st_nlink == 1,
            'Expected an owned single-link mode0600 baseline receipt')
    # Renaming consumes the original once before validation. Invalid receipts do
    # not become reusable; concurrent consumers cannot both rename the source.
    os.rename(path, consumed)
    fd = os.open(consumed, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    with os.fdopen(fd, 'rb') as stream:
        st = os.fstat(stream.fileno())
        require(stat.S_ISREG(st.st_mode) and st.st_uid == os.getuid() and
                stat.S_IMODE(st.st_mode) == 0o600 and st.st_nlink == 1 and st.st_size < 8192,
                'Receipt is not an owned single-link mode0600 bounded regular file')
        raw = stream.read()
    receipt = json.loads(raw)
    require(isinstance(receipt, dict), 'Receipt must be a JSON object')
    require(receipt.get('kind') == 'ABSENT_SERIAL_BASELINE_ONLY' and receipt.get('serial') == SERIAL,
            'Wrong baseline receipt contract')
    require(receipt.get('snapshot') == 'baseline-ioreg.plist', 'Unexpected baseline snapshot path')
    created = receipt.get('created_monotonic')
    require(type(created) in (float, int), 'Invalid receipt monotonic timestamp')
    age = time.monotonic() - created
    require(0 <= age <= 180 and receipt.get('expires_after_seconds') == 180,
            'Baseline receipt expired or monotonic time is inconsistent')
    require(receipt.get('host_boot_fingerprint') == host_boot_fingerprint(deadline),
            'Baseline host or boot epoch differs')
    source = consumed.parent / 'baseline-ioreg.plist'
    fd = os.open(source, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    with os.fdopen(fd, 'rb') as stream:
        st = os.fstat(stream.fileno())
        require(stat.S_ISREG(st.st_mode) and st.st_uid == os.getuid() and st.st_nlink == 1 and
                not (st.st_mode & 0o022) and st.st_size <= 64 * 1024 * 1024,
                'Invalid baseline snapshot file')
        snapshot_raw = stream.read()
    require(hashlib.sha256(snapshot_raw).hexdigest() == receipt.get('snapshot_sha256'),
            'Baseline snapshot hash mismatch')
    tree = plistlib.loads(snapshot_raw)
    require(not any(n.get('USB Serial Number') == SERIAL for n in walk(tree)),
            'Baseline snapshot did not establish serial absence')
    write_private(output / 'baseline-ioreg.plist', snapshot_raw)
    write_private(output / 'consumed-baseline-receipt.json', raw)
    return {'source': str(consumed.resolve()), 'age_seconds': round(age, 3),
            'snapshot_sha256': receipt['snapshot_sha256']}


RAW_READER = '''import os, re, stat, sys
path=sys.argv[1]
if not re.fullmatch(r'/dev/rdisk[0-9]+',path): raise SystemExit('invalid raw path')
fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
try:
 if not stat.S_ISCHR(os.fstat(fd).st_mode): raise SystemExit('not a raw character device')
 chunks=[]; left=65536
 while left:
  block=os.read(fd,left)
  if not block: raise SystemExit('short raw read')
  chunks.append(block); left-=len(block)
 sys.stdout.buffer.write(b''.join(chunks))
finally: os.close(fd)
'''


VOLUME_READER = '''import json, runpy, sys
module = runpy.run_path(sys.argv[1])
print(json.dumps(module['read_volume_report'](sys.argv[2])))
'''


def collect_volume_report(output, info, observed, disk_args, deadline):
    if not info.get('MountPoint'):
        command(['/usr/sbin/diskutil', 'mount', 'readOnly', '/dev/' + observed['disk']],
                deadline, record_path=output / 'mount-command.json')
    else:
        write_private(output / 'mount-command.json',
                      b'{"action":"existing mount; no explicit mount command"}\n')
    current_raw = command(disk_args, deadline)
    write_private(output / 'diskutil-mounted.plist', current_raw)
    current = plistlib.loads(current_raw)
    mountpoint, state = validate_mountpoint(current, observed)
    require(current.get('VolumeName') == 'RAMPROBE', 'Mounted volume label differs')
    require(select_media(snapshot(output, 'volume-preread-ioreg', deadline)) == observed,
            'Registry identity changed before mounted report read')
    reader_raw = command([sys.executable, '-c', VOLUME_READER, str(Path(__file__).resolve()), mountpoint],
                         deadline, 8192)
    details = json.loads(reader_raw)
    require(details.get('mountpoint') == mountpoint and details.get('filesystem_readonly') is True,
            'Volume reader did not establish exact read-only mount')
    report = details.pop('report_text').encode('ascii')
    fields = parse_report(report)
    write_private(output / 'REPORT.TXT', report)
    write_private(output / 'volume-read.json', (json.dumps(details, indent=2) + '\n').encode())
    return fields, mountpoint, state, details


def observe(output, seconds, baseline_receipt=None, report_via_volume=False):
    require(sys.platform == 'darwin', '--observe requires macOS')
    require(not output.exists(), 'Evidence directory must not already exist')
    output.mkdir(parents=True, mode=0o700)
    started = time.monotonic()
    deadline = started + seconds
    result = {'status': 'INCONCLUSIVE', 'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'host_deadline_seconds': seconds, 'minimal_discriminator_positive': False,
              'normal_android_return_proven': False, 'automount_prevented': False,
              'observation_mode': 'readonly-volume-report' if report_via_volume else 'raw-media',
              'raw_FAT_verified': False,
              'acceptance_adjustment': 'Parent accepts actual read-only media plus exact report observation; '
              'automatic mount history is not attested. Positive means minimal kernel/PID1/RAMUSB only.'}
    try:
        if baseline_receipt is not None:
            result['baseline_receipt'] = consume_baseline(baseline_receipt, output, deadline)
            print('OBSERVING: fresh baseline receipt consumed; host deadline is running.', flush=True)
        else:
            baseline = snapshot(output, 'baseline-ioreg', deadline)
            require(not any(n.get('USB Serial Number') == SERIAL for n in walk(baseline)),
                    'Serial already present at baseline; freshness is unproven')
            print('ARMED: baseline serial absent. Parent may now perform separately authorized manual entry.', flush=True)
        observed = None
        last_wait_reason = None
        sequence = 0
        while remaining(deadline):
            sequence += 1
            tree = snapshot(output, 'latest-poll-ioreg', deadline)
            if devices(tree):
                try:
                    observed = select_media(tree)
                    break
                except Refused as exc:
                    # USB/driver children can be incomplete during enumeration.
                    # Such a snapshot never permits a disk access.
                    last_wait_reason = str(exc)
            time.sleep(min(0.5, remaining(deadline)))
        require(observed is not None, 'No complete identity: ' + str(last_wait_reason))
        result['identity'] = observed
        disk_args = ['/usr/sbin/diskutil', 'info', '-plist', '/dev/' + observed['disk']]
        info_raw = command(disk_args, deadline)
        write_private(output / 'diskutil-before.plist', info_raw)
        info = plistlib.loads(info_raw)
        result['mount_state_before'] = verify_disk(info, observed)
        require(select_media(snapshot(output, 'preread-ioreg', deadline)) == observed,
                'Registry identity changed before report access')
        if report_via_volume:
            fields, mountpoint, state, details = collect_volume_report(output, info, observed, disk_args, deadline)
            result['mount_state_at_read'] = state
            result['volume_read'] = details
        else:
            raw = command([sys.executable, '-c', RAW_READER, '/dev/r' + observed['disk']], deadline, 65536)
            write_private(output / 'media.raw', raw)
            fields, report = parse_fat(raw)
            write_private(output / 'REPORT.TXT', report)
        require(select_media(snapshot(output, 'postread-ioreg', deadline)) == observed,
                'Registry identity changed during report access')
        after_raw = command(disk_args, deadline)
        write_private(output / 'diskutil-after.plist', after_raw)
        after = plistlib.loads(after_raw)
        result['mount_state_after'] = verify_disk(after, observed)
        if report_via_volume:
            after_mountpoint, _ = validate_mountpoint(after, observed)
            require(after_mountpoint == mountpoint and after.get('VolumeName') == 'RAMPROBE',
                    'Exact device mountpoint or volume changed after report read')
            result.update(status='POSITIVE_PID1_REPORT_VIA_READONLY_VOLUME', raw_FAT_verified=False)
        else:
            result.update(status='POSITIVE_MINIMAL_PID1_DISCRIMINATOR', raw_FAT_verified=True,
                          media_sha256=hashlib.sha256(raw).hexdigest())
        result.update(minimal_discriminator_positive=True, report=fields, fresh_usb_transition=True)
    except (Refused, OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired) as exc:
        result['reason'] = str(exc)
    finally:
        result['elapsed_seconds'] = round(time.monotonic() - started, 3)
        write_private(output / 'result.json', (json.dumps(result, indent=2) + '\n').encode())
    print(json.dumps(result, indent=2))
    return 0 if result['minimal_discriminator_positive'] else 2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument('--observe', action='store_true', help='Live read-only observation; requires parent trial authorization')
    modes.add_argument('--baseline-only', action='store_true', help='Live absent-serial baseline and single-use 180s receipt')
    parser.add_argument('--baseline-receipt', type=Path, help='Consume prior baseline; begin bound after parent entry confirmation')
    parser.add_argument('--report-via-volume', action='store_true',
                        help='Explicit alternative: exact read-only mounted REPORT.TXT; permits exact diskutil mount readOnly only')
    parser.add_argument('--output', type=Path, default=BASE / 'evidence/live-trial')
    parser.add_argument('--seconds', type=float, default=55, help='Host bound, maximum 60 seconds; includes baseline')
    args = parser.parse_args()
    require(0 < args.seconds <= 60, 'seconds must be positive and at most 60')
    require(args.baseline_receipt is None or args.observe, '--baseline-receipt requires --observe')
    require(not args.report_via_volume or args.observe, '--report-via-volume requires --observe')
    if args.baseline_only:
        return baseline_only(args.output)
    if not args.observe:
        print('PLAN_ONLY: no ioreg, diskutil, device read, mount, unmount, repair, write, or sudo executed.\n'
              'See README.md; live opt-in is --observe --output <new evidence directory>.\n'
              'Arm before manual recovery entry. Raw reads require exact fresh USB identity, 65536B, IOMedia Writable=false.')
        return 0
    return observe(args.output, args.seconds, args.baseline_receipt, args.report_via_volume)


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Refused as exc:
        raise SystemExit('REFUSED: ' + str(exc))
