#!/usr/bin/env python3
"""Read a fixed ASUS LK partition; never download, erase, flash or unlock.

The stock 5.3.20 handler streams raw bytes, without a DATA frame, then OKAY.
Require agreement between Android GPT evidence, the live LK partition listing
and getvar before receiving exactly that many bytes into a private local file.
"""
import argparse
import datetime
import hashlib
import json
import os
import re
import shutil
import time
from pathlib import Path

import usb.backend.libusb1
import usb.core
import usb.util

ROOT = Path(__file__).resolve().parents[1]
PARTITIONS = ('boot1', 'boot2', 'boot', 'recovery', 'lk', 'proinfo', 'nvram', 'protect1',
              'protect2', 'asus_nvm', 'persist', 'seccfg', 'secro', 'para',
              'tee1', 'tee2')
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('partition', choices=PARTITIONS)
parser.add_argument('--execute', action='store_true')
parser.add_argument('--tag', required=True, type=lambda s: s if re.fullmatch(r'[a-zA-Z0-9_-]+', s) else parser.error('Invalid tag'))
args = parser.parse_args()
os.umask(0o077)
directory = ROOT / 'artifacts/device-backup' / args.tag
directory.mkdir(parents=True, exist_ok=True, mode=0o700)
output = directory / (args.partition + '.bin')
partial = directory / (args.partition + '.bin.partial')
assert not output.exists() and not partial.exists(), 'Refusing to overwrite a backup'
log = (directory / (args.partition + '.jsonl')).open('x', buffering=1)


def event(phase, **data):
    line = json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), phase=phase, **data))
    log.write(line + '\n')
    print(line, flush=True)


device = None
claimed = False
try:
    bootarea = args.partition in ('boot1', 'boot2')
    old = json.loads((ROOT.parent / '2026-11-05-asus-latest-android-feasibility/evidence/live-partition-layout.json').read_text())
    expected = next((p for p in old if p['name'] == args.partition), None)
    records = [json.loads(s) for s in (ROOT / 'evidence/fastboot-partition-list.jsonl').read_text().splitlines()]
    assert any(r['phase'] == 'query_complete' and r['success'] for r in records)
    matching = []
    for record in records:
        if record['phase'] != 'response' or record['prefix'] != 'INFO':
            continue
        match = re.fullmatch(r'ptn\[\d+\] (\S+) (\d+) N/A (\d+) (\d+)', record['payload'])
        if match and match[1] == args.partition:
            matching.append(tuple(map(int, match.group(2, 3, 4))))
    if bootarea:
        # Matching live LK handlers 0x41e224a4 / 0x41e225b4 read precisely
        # 0x400000 bytes from eMMC area 1 / 2, in 0x10000-byte chunks.
        comparison = json.loads((ROOT / 'evidence/live-lk-official-comparison.json').read_text())
        assert comparison['official_lk_exact_prefix']
        size = 0x400000
        event('fixed_bootarea_handler', area=args.partition, bytes=size, source='matching live LK disassembly; not a GPT partition')
    else:
        assert matching == [(expected['sectors'], expected['start_sector'], expected['start_sector'] + expected['sectors'] - 1)], matching
        size = expected['size_bytes']
    assert 0 < size <= 64 * 1024 * 1024 and size % 512 == 0
    assert shutil.disk_usage(directory).free > size + 1024 * 1024 * 1024
    event('plan', partition=args.partition, size=size, start_sector=expected['start_sector'] if expected else None, execute=args.execute)
    if not args.execute:
        raise SystemExit(0)
    backend = usb.backend.libusb1.get_backend(find_library=lambda _: '/opt/homebrew/lib/libusb-1.0.dylib')
    candidates = [d for d in usb.core.find(find_all=True, idVendor=0x0bb4, idProduct=0x0c01, backend=backend)
                  if d.serial_number == 'DEVICE_SERIAL_REDACTED']
    assert len(candidates) == 1, 'Exact ASUS fastboot device required'
    device = candidates[0]
    interfaces = [i for i in device.get_active_configuration()
                  if (i.bInterfaceClass, i.bInterfaceSubClass, i.bInterfaceProtocol) == (0xff, 0x42, 3)]
    assert len(interfaces) == 1
    interface = interfaces[0]
    endpoints = [e for e in interface if usb.util.endpoint_type(e.bmAttributes) == usb.util.ENDPOINT_TYPE_BULK]
    inputs = [e for e in endpoints if usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_IN]
    outputs = [e for e in endpoints if usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_OUT]
    assert len(inputs) == len(outputs) == 1
    ep_in, ep_out = inputs[0], outputs[0]
    usb.util.claim_interface(device, interface.bInterfaceNumber)
    claimed = True

    def write(command):
        event('command', value=command.decode('ascii'))
        assert len(command) <= 64
        assert ep_out.write(command, timeout=1500) == len(command)

    if not bootarea:
        write(('getvar:partition-size:' + args.partition).encode('ascii'))
        for _ in range(16):
            response = bytes(ep_in.read(64, timeout=2500))
            if response.startswith(b'INFO'):
                continue
            assert response.startswith(b'OKAY'), repr(response)
            assert int(response[4:], 16) == size, (response, size)
            break
        else:
            raise RuntimeError('No size response')

    command = 'oem emmc_read_' + args.partition if bootarea else 'oem emmc_read_partition ' + args.partition
    write(command.encode('ascii'))
    deadline = time.monotonic() + 90
    digest = hashlib.sha256()
    count = 0
    with partial.open('xb') as stream:
        while count < size:
            if time.monotonic() > deadline:
                raise TimeoutError('Total read deadline exceeded')
            chunk = bytes(ep_in.read(min(65536, size - count), timeout=5000))
            assert chunk, 'Empty transfer'
            if count == 0 and len(chunk) < 64 and chunk.startswith((b'FAIL', b'INFO', b'OKAY')):
                raise RuntimeError('Expected raw partition, received protocol reply: ' + repr(chunk))
            stream.write(chunk)
            digest.update(chunk)
            count += len(chunk)
        stream.flush()
        os.fsync(stream.fileno())
    response = bytes(ep_in.read(64, timeout=2500))
    assert response == b'OKAY', ('Missing terminal OKAY', response)
    partial.rename(output)
    event('backup_complete', partition=args.partition, bytes=count, sha256=digest.hexdigest(), output=str(output))
except Exception as exc:
    event('error', type=type(exc).__name__, message=str(exc))
    raise SystemExit(2)
finally:
    if claimed:
        try:
            usb.util.release_interface(device, interface.bInterfaceNumber)
        except Exception as exc:
            event('release_error', message=str(exc))
    if device is not None:
        usb.util.dispose_resources(device)
    log.close()
