#!/usr/bin/env python3
"""Observe one manual recovery control. Read-only ADB; never reboots or writes."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

SERIAL = 'DEVICE_SERIAL_REDACTED'
ROOT = Path(__file__).resolve().parents[1]


def command(args):
    return subprocess.run(['adb', *args], capture_output=True, timeout=12, check=False)


def main():
    os.umask(0o077)
    destination = ROOT / 'artifacts/private' / datetime.datetime.now(datetime.timezone.utc).strftime('control-%Y%m%dT%H%M%SZ')
    destination.mkdir(parents=True, exist_ok=False)
    last = None
    complete = False
    end = time.monotonic() + 420
    with (destination / 'events.jsonl').open('x') as log:
        def event(kind, **fields):
            value = dict(time=datetime.datetime.now(datetime.timezone.utc).isoformat(), kind=kind, **fields)
            line = json.dumps(value)
            log.write(line + '\n')
            log.flush()
            print(line, flush=True)
        event('observer_started', evidence=str(destination), device_mutations=False)
        while time.monotonic() < end:
            try:
                result = command(['devices'])
                states = dict(line.split()[:2] for line in result.stdout.decode(errors='replace').splitlines()[1:] if len(line.split()) >= 2)
                state = states.get(SERIAL, 'absent')
                if state != last:
                    event('adb_state', state=state)
                    last = state
                if state == 'recovery' and not complete:
                    result = command(['-s', SERIAL, 'shell', 'report'])
                    if b'ASUS RAM-only diagnostic v1' in result.stdout:
                        (destination / 'diagnostic-report.txt').write_bytes(result.stdout)
                        complete = b'END_DIAGNOSTIC' in result.stdout and result.returncode == 0
                        event('diagnostic_marker', complete=complete, bytes=len(result.stdout),
                              sha256=hashlib.sha256(result.stdout).hexdigest())
                elif state == 'device' and complete:
                    sdk = command(['-s', SERIAL, 'shell', 'getprop', 'ro.build.version.sdk'])
                    boot = command(['-s', SERIAL, 'shell', 'getprop', 'sys.boot_completed'])
                    if sdk.stdout.strip() == b'24' and boot.stdout.strip() == b'1':
                        event('stock_android_returned', sdk=24, boot_completed=True,
                              recovery_restored=False, next='Run exact stock recovery restore and verification')
                        return
            except (subprocess.TimeoutExpired, OSError) as error:
                event('observation_error', error=str(error))
            time.sleep(2)
        event('observation_deadline', report_complete=complete,
              next='Assess screen/USB and use physical Normal Boot; do not infer rejection or restoration')
        raise SystemExit(2)


if __name__ == '__main__':
    main()
