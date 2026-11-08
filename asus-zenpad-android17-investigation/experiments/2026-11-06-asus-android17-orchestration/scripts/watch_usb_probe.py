"""Observe one fresh USB probe identity on the known tablet port; never write to it."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import plistlib
import stat
import subprocess
import time


def devices(value):
    if isinstance(value, dict):
        if 'USBDeviceKeySerialNumber' in value:
            yield {k: v for k, v in value.items() if not isinstance(v, (dict, list))}
        for child in value.values():
            yield from devices(child)
    elif isinstance(value, list):
        for child in value:
            yield from devices(child)


def number(value):
    try:
        return int(str(value).split()[0], 0)
    except (ValueError, IndexError):
        return None


def collect_report(output):
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        try:
            result = subprocess.run(['diskutil', 'list', '-plist', 'external', 'physical'],
                                    capture_output=True, timeout=6)
            listing = plistlib.loads(result.stdout)
            candidates = [d for d in listing.get('AllDisksAndPartitions', [])
                          if 65536 <= d.get('Size', 0) <= 4 * 1024 * 1024]
            if len(candidates) == 1:
                disk = candidates[0]
                info_result = subprocess.run(
                    ['diskutil', 'info', '-plist', '/dev/' + disk['DeviceIdentifier']],
                    capture_output=True, timeout=6)
                info = plistlib.loads(info_result.stdout)
                if info.get('BusProtocol', info.get('Protocol')) == 'USB':
                    for volume in [disk, *disk.get('Partitions', [])]:
                        mount = volume.get('MountPoint')
                        if not isinstance(mount, str) or not mount.startswith('/Volumes/'):
                            continue
                        source = Path(mount) / 'PROBE.TXT'
                        fd = os.open(source, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
                        try:
                            before = os.fstat(fd)
                            if not stat.S_ISREG(before.st_mode) or not 0 < before.st_size <= 4096:
                                continue
                            data = os.read(fd, 4097)
                            after = os.fstat(fd)
                            if (len(data) != before.st_size or
                                    (before.st_dev, before.st_ino, before.st_size) !=
                                    (after.st_dev, after.st_ino, after.st_size)):
                                continue
                        finally:
                            os.close(fd)
                        with output.open('xb') as stream:
                            stream.write(data)
                            stream.flush()
                            os.fsync(stream.fileno())
                        return dict(outcome='ram_usb_report_file_observed',
                                    disk=disk['DeviceIdentifier'], bytes=len(data),
                                    sha256=hashlib.sha256(data).hexdigest(), output=str(output))
        except (OSError, ValueError, KeyError, plistlib.InvalidFileException,
                subprocess.TimeoutExpired):
            pass
        time.sleep(1)
    return dict(outcome='usb_identity_observed_but_report_file_not_collected')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--serial', required=True)
    parser.add_argument('--vid', required=True, type=lambda s: int(s, 0))
    parser.add_argument('--pid', required=True, type=lambda s: int(s, 0))
    parser.add_argument('--location', default='0x01111000')
    parser.add_argument('--seconds', type=int, default=180)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--report-output', type=Path)
    args = parser.parse_args()
    if not 5 <= args.seconds <= 600 or args.output.exists():
        parser.error('Use a bounded observation window and a fresh output path')
    if args.report_output and args.report_output.exists():
        parser.error('Use a fresh report output path')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    state = dict(started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                 serial=args.serial, location=args.location, read_only=True,
                 outcome='observation_deadline_without_match', rejected_matches=[])
    print(json.dumps(dict(observer_started=True, serial=args.serial,
                          receipt=str(args.output))), flush=True)
    deadline = time.monotonic() + args.seconds
    while time.monotonic() < deadline:
        try:
            result = subprocess.run(['system_profiler', '-json', 'SPUSBHostDataType'],
                                    capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                matches = [d for d in devices(json.loads(result.stdout))
                           if d.get('USBDeviceKeySerialNumber') == args.serial]
                if len(matches) == 1:
                    device = matches[0]
                    if (number(device.get('USBDeviceKeyVendorID')) == args.vid and
                            number(device.get('USBDeviceKeyProductID')) == args.pid and
                            device.get('USBKeyLocationID') == args.location):
                        state.update(outcome='matching_usb_device_observed', device=device)
                        if args.report_output:
                            state['report_capture'] = collect_report(args.report_output)
                        break
                    if len(state['rejected_matches']) < 8:
                        state['rejected_matches'].append(device)
        except (subprocess.TimeoutExpired, UnicodeError, ValueError):
            pass
        time.sleep(2)
    state['ended_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with args.output.open('x') as stream:
        json.dump(state, stream, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    print(json.dumps(state), flush=True)
    return 0 if state['outcome'] == 'matching_usb_device_observed' else 2


if __name__ == '__main__':
    raise SystemExit(main())
