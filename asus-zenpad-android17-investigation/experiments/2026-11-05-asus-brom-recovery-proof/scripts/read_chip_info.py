#!/usr/bin/env python3
"""Bounded MediaTek BROM serial handshake and three fixed metadata queries.

No watchdog/register writes, RAM payload, DA, reset, unlock or flash commands.
Protocol: pinned mtkclient Port.py and mtk_preloader.py (see source manifest).
"""
import argparse
import datetime
import json
import struct
import time
from pathlib import Path

import serial
import serial.tools.list_ports

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--log', type=Path, required=True)
p.add_argument('--wait', type=int, default=120, choices=range(1, 181))
p.add_argument('--include-preloader', action='store_true', help='Also query PID 2000 and distinguish it using GET_BL_VER')
a = p.parse_args()
log = a.log.open('x', buffering=1)


def event(phase, **values):
    line = json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), phase=phase, **values))
    log.write(line + '\n')
    print(line, flush=True)


def read_exact(port, count):
    result = b''
    end = time.monotonic() + 1.5
    while len(result) < count and time.monotonic() < end:
        result += port.read(count - len(result))
    if len(result) != count:
        raise TimeoutError(f'Expected {count} bytes, received {result.hex()}')
    return result


try:
    allowed_pids = (0x0003, 0x2000) if a.include_preloader else (0x0003,)
    event('waiting', usb_ids=[f'0e8d:{x:04x}' for x in allowed_pids], seconds=a.wait)
    deadline = time.monotonic() + a.wait
    last_seen = set()
    while time.monotonic() < deadline:
        ports = list(serial.tools.list_ports.comports())
        known = [x for x in ports if x.vid == 0x0e8d]
        for port in known:
            key = (port.device, port.pid)
            if key not in last_seen:
                event('mediatek_serial', path=port.device, product_id=hex(port.pid), location=port.location)
                last_seen.add(key)
        candidates = [x for x in known if x.pid in allowed_pids]
        if len(candidates) > 1:
            raise RuntimeError('Ambiguous MediaTek BROM devices; refusing')
        if not candidates:
            time.sleep(0.15)
            continue
        selected = candidates[0]
        event('opening', path=selected.device, baud=115200)
        with serial.Serial(selected.device, baudrate=115200, timeout=0.15, write_timeout=0.5,
                           xonxoff=False, dsrdtr=False, rtscts=False) as port:
            for attempt in range(3):
                try:
                    for value in (0xa0, 0x0a, 0x50, 0x05):
                        port.write(bytes([value]))
                        response = read_exact(port, 1)
                        if value == 0xa0 and response == b'R' and selected.pid == 0x2000:
                            notification = response + read_exact(port, 4)
                            if notification != b'READY':
                                raise RuntimeError('Unexpected startup notification: ' + notification.hex())
                            event('preloader_startup', notification='READY')
                            response = read_exact(port, 1)
                        if response != bytes([value ^ 0xff]):
                            raise RuntimeError('Handshake echo mismatch: ' + response.hex())
                    break
                except (TimeoutError, RuntimeError) as exc:
                    event('handshake_retry', attempt=attempt + 1, error=str(exc))
                    if attempt == 2:
                        raise
            event('handshake_complete')

            def query(command, count):
                if command not in (0xfd, 0xfc, 0xd8):
                    raise RuntimeError('Command is not a fixed read-only metadata query')
                port.write(bytes([command]))
                if read_exact(port, 1) != bytes([command]):
                    raise RuntimeError('Query echo mismatch')
                result = read_exact(port, count)
                event('reply', command=hex(command), raw_hex=result.hex())
                return result

            hwcode, hwversion = struct.unpack('>HH', query(0xfd, 4))
            if hwcode != 0x8163:
                raise RuntimeError(f'Expected MT8163, found {hwcode:04x}; stopping')
            target, status = struct.unpack('>IH', query(0xd8, 6))
            if status:
                raise RuntimeError(f'Target configuration status {status:04x}')
            subcode, version, software, status = struct.unpack('>HHHH', query(0xfc, 8))
            if status:
                raise RuntimeError(f'Hardware version status {status:04x}')
            # Unlike the queries above, FE returns the PL version without an
            # echo, or echoes FE when the immutable BROM handles the command.
            port.write(b'\xfe')
            boot_version = read_exact(port, 1)[0]
            event('chip_info_complete', hwcode=hex(hwcode), initial_version=hex(hwversion),
                  subcode=hex(subcode), hardware_version=hex(version), software_version=hex(software),
                  target_configuration=hex(target), secure_boot=bool(target & 1),
                  serial_link_auth=bool(target & 2), download_agent_auth=bool(target & 4),
                  observed_stage='brom' if boot_version == 0xfe else 'preloader', boot_version=hex(boot_version),
                  flash_or_ram_writes=False)
        break
    else:
        raise TimeoutError('No BROM serial interface appeared before deadline')
except Exception as exc:
    event('error', type=type(exc).__name__, message=str(exc))
    raise SystemExit(2)
finally:
    log.close()
