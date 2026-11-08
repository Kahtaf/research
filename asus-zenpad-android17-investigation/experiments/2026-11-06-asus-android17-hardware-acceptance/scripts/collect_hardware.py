#!/usr/bin/env python3
"""Bounded read-only evidence collection for the actual ASUS Android17 port."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess

SERIAL = 'DEVICE_SERIAL_REDACTED'
ROOT = Path(__file__).resolve().parents[1]
COMMANDS = {
    'identity': 'getprop ro.product.device; getprop ro.product.model; getprop ro.build.fingerprint; getprop ro.build.version.sdk; getprop ro.product.first_api_level; uname -a; id; getenforce',
    'boot': 'getprop sys.boot_completed; getprop init.svc.zygote; getprop init.svc.surfaceflinger; getprop init.svc.bootanim; uptime',
    'display': 'dumpsys display',
    'surfaceflinger': 'dumpsys SurfaceFlinger',
    'input': 'dumpsys input; cat /proc/bus/input/devices',
    'wifi': 'dumpsys wifi',
    'bluetooth': 'dumpsys bluetooth_manager',
    'battery': 'dumpsys battery',
    'thermal': 'dumpsys thermalservice',
    'health': 'service list; lshal',
    'memory': 'cat /proc/meminfo; cat /proc/swaps; cat /proc/pressure/memory',
    'storage': 'cat /proc/mounts; df -k /data /system /vendor /product /system_ext',
    'google': 'pm path com.google.android.gms; pm path com.android.vending; pm path com.google.android.gsf; dumpsys apexservice',
    'power-supply': 'for d in /sys/class/power_supply/*; do echo "SUPPLY $d"; for f in type status health present capacity voltage_now current_now temp online charge_type; do if [ -r "$d/$f" ]; then echo "$f=$(cat "$d/$f")"; fi; done; done',
}


def adb(command, timeout):
    return subprocess.run(['adb', '-s', SERIAL, 'shell', command],
                          capture_output=True, timeout=timeout, check=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', action='store_true', help='Print commands without contacting ADB')
    args = parser.parse_args()
    if args.plan:
        print(json.dumps(dict(serial=SERIAL, expected_sdk=37, device_writes=False,
                              commands=COMMANDS), indent=2))
        return
    sdk = adb('getprop ro.build.version.sdk', 12)
    if sdk.returncode or sdk.stdout.strip() != b'37':
        raise SystemExit('Exact ASUS must be reachable and running SDK37. No evidence session created.')
    identity = adb('getprop ro.product.device; getprop ro.product.model', 12)
    if identity.returncode or not any(x in identity.stdout.lower() for x in (b'p00a', b'z380m')):
        raise SystemExit('ASUS product identity mismatch. No evidence session created.')
    os.umask(0o077)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    destination = ROOT / 'artifacts/private' / stamp
    destination.mkdir(parents=True, exist_ok=False, mode=0o700)
    records = []
    for name, command in COMMANDS.items():
        row = dict(name=name, command=command, timeout_seconds=30)
        try:
            process = adb(command, 30)
            stdout, stderr = process.stdout, process.stderr
            row.update(exit_code=process.returncode, timed_out=False)
        except subprocess.TimeoutExpired as error:
            stdout, stderr = error.stdout or b'', error.stderr or b''
            row.update(exit_code=None, timed_out=True)
        # Restrict retained output; dumpsys content can vary substantially.
        limit = 4 * 1024 * 1024
        row['output_truncated'] = len(stdout) > limit or len(stderr) > limit
        for label, data in (('stdout', stdout[:limit]), ('stderr', stderr[:limit])):
            path = destination / (name + '.' + label + '.txt')
            path.write_bytes(data)
            row[label] = dict(path=path.name, bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
        records.append(row)
        print(f'{name}: exit={row["exit_code"]}, timeout={row["timed_out"]}', flush=True)
    report = dict(serial=SERIAL, expected_sdk=37, sdk_guard_passed=True,
                  product_identity=identity.stdout.decode(errors='replace').strip(),
                  created_at=stamp, device_mutations=False, observations=records,
                  functional_hardware_pass=False, google_runtime_pass=False,
                  note='Read-only observations. Functional display/touch/radio/charging/Play tests remain required.')
    (destination / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(str(destination / 'report.json'))


if __name__ == '__main__':
    main()
