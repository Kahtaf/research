#!/usr/bin/env python3
"""Request only FASTBOOT through the observed stock preloader READY protocol.

The fixed command, acknowledgement and DISCONNECT occur in the exact stock
preloader and pinned mtkclient META implementation. No payload/storage command.
"""
import argparse
import datetime
import json
import time
from pathlib import Path

import serial
import serial.tools.list_ports
import usb.core
import usb.backend.libusb1

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--location', required=True, help='Previously observed exact USB location')
a = p.parse_args()
root = Path(__file__).resolve().parents[1]
tag = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
log = (root / f'evidence/fastboot-mode-{tag}.jsonl').open('x', buffering=1)


def event(phase, **values):
    line = json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), phase=phase, **values))
    log.write(line + '\n')
    print(line, flush=True)


def receive_until(port, token):
    received = bytearray()
    deadline = time.monotonic() + 2
    while time.monotonic() < deadline and len(received) < 1024:
        received.extend(port.read(min(64, 1024 - len(received))))
        if b'METASLA' in received:
            raise RuntimeError('Authentication challenge; no authentication reply sent')
        if token in received:
            event('received', token=token.decode('ascii'), raw_hex=received.hex())
            return
    raise RuntimeError('Expected token not received: ' + token.decode('ascii') + '; raw=' + received.hex())


def confirm_fastboot():
    backend = usb.backend.libusb1.get_backend(find_library=lambda _: '/opt/homebrew/lib/libusb-1.0.dylib')
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        devices = [d for d in usb.core.find(find_all=True, idVendor=0x0bb4, idProduct=0x0c01, backend=backend)
                   if d.serial_number == 'DEVICE_SERIAL_REDACTED']
        if len(devices) > 1:
            raise RuntimeError('Ambiguous ASUS fastboot serial')
        if devices:
            interfaces = [i for i in devices[0].get_active_configuration()
                          if (i.bInterfaceClass, i.bInterfaceSubClass, i.bInterfaceProtocol) == (0xff, 0x42, 3)]
            if len(interfaces) != 1:
                raise RuntimeError('Unexpected ASUS fastboot interface')
            event('fastboot_mode_confirmed', serial='DEVICE_SERIAL_REDACTED', interface='ff/42/03')
            return
        time.sleep(0.1)
    raise RuntimeError('Mode request was not confirmed by exact ASUS fastboot enumeration')


try:
    event('waiting', seconds=120, vid='0e8d', pid='2000', location=a.location)
    deadline = time.monotonic() + 120
    while time.monotonic() < deadline:
        devices = [d for d in serial.tools.list_ports.comports()
                   if d.vid == 0x0e8d and d.pid == 0x2000 and d.location == a.location]
        if len(devices) > 1:
            raise RuntimeError('Ambiguous physical target')
        if not devices:
            time.sleep(0.05)
            continue
        device = devices[0]
        port = serial.Serial(port=None, baudrate=921600, timeout=0.05, write_timeout=0.5,
                             xonxoff=False, dsrdtr=False, rtscts=False)
        port.dtr = False
        port.rts = True
        port.port = device.device
        request_sent = False
        try:
            with port:
                event('opened', path=device.device, location=device.location)
                receive_until(port, b'READY')
                if port.write(b'FASTBOOT') != 8:
                    raise RuntimeError('Short FASTBOOT request')
                request_sent = True
                event('mode_requested', command='FASTBOOT')
                receive_until(port, b'TOOBTSAF')
                if port.write(b'DISCONNECT') != 10:
                    raise RuntimeError('Short disconnect request')
                event('mode_request_acknowledged', storage_or_payload_commands=False)
        except (serial.SerialException, OSError) as exc:
            if not request_sent:
                raise
            # This exact unit switched immediately after FASTBOOT, dropping
            # the serial interface before a textual acknowledgement arrived.
            event('serial_disconnected_after_request', message=str(exc), success_unconfirmed=True)
        confirm_fastboot()
        break
    else:
        raise TimeoutError('No preloader on the expected physical USB port')
except Exception as exc:
    event('error', type=type(exc).__name__, message=str(exc))
    raise SystemExit(2)
finally:
    log.close()
