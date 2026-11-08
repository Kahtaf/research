#!/usr/bin/env python3
"""Test one handshake byte with upstream-native-equivalent CDC settings.

No chip query, watchdog change, reset, payload, DA or storage command is sent.
This tests the recorded transport premise without assuming handshake success.
"""
import datetime
import argparse
import json
import time
from pathlib import Path

import serial
import serial.tools.list_ports

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--wait', type=int, choices=range(1, 181), default=60)
args = parser.parse_args()
tag = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
log = (root / f'evidence/serial-control-{tag}.jsonl').open('x', buffering=1)


def event(phase, **values):
    line = json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), phase=phase, **values))
    log.write(line + '\n')
    print(line, flush=True)


try:
    event('waiting', seconds=args.wait, vid='0e8d', pids=['0003', '2000'])
    deadline = time.monotonic() + args.wait
    while time.monotonic() < deadline:
        ports = [p for p in serial.tools.list_ports.comports() if p.vid == 0x0e8d and p.pid in (3, 0x2000)]
        if len(ports) > 1:
            raise RuntimeError('Ambiguous MediaTek interfaces')
        if not ports:
            time.sleep(0.05)
            continue
        selected = ports[0]
        port = serial.Serial(port=None, baudrate=921600, timeout=0.05, write_timeout=0.5,
                             xonxoff=False, dsrdtr=False, rtscts=False)
        port.dtr = False
        port.rts = True
        port.port = selected.device
        with port:
            event('opened', path=selected.device, location=selected.location,
                  pid=hex(selected.pid), baud=921600, dtr=False, rts=True)
            if port.write(b'\xa0') != 1:
                raise RuntimeError('Short handshake write')
            received = bytearray()
            end = time.monotonic() + 2
            while time.monotonic() < end and len(received) < 256:
                received.extend(port.read(min(64, 256 - len(received))))
                if 0x5f in received:
                    break
            event('observation', transmitted_hex='a0', received_hex=received.hex(),
                  expected_complement_seen=0x5f in received, complete_handshake=False,
                  chip_queries_or_memory_storage_writes=False)
        break
    else:
        raise TimeoutError('No matching serial interface appeared')
except Exception as exc:
    event('error', type=type(exc).__name__, message=str(exc))
    raise SystemExit(2)
finally:
    log.close()
