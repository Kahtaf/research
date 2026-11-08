"""Observe only the fixed stock ASUS; never connect, reboot, root or write it."""
from pathlib import Path
import datetime
import fcntl
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
BRIDGE = WORKSPACE / '2026-11-06-asus-usb-observation-dispatch-fix/source/transport.py'
BRIDGE_SHA = '27b8fbf665e8efd5b41b6485184393f112eb7c6fe6854a6821d0f14a84f785d8'
ADB = Path('/opt/homebrew/Caskroom/android-platform-tools/37.0.1/platform-tools/adb')
ADB_SHA = '1811e253b21b12cbfda7201ebaf86c10e7ddcb5c606a7a81f7c82b4c429c2d3b'
ENDPOINT = 'IP_REDACTED:5555'
FINGERPRINT = 'asus/WW_P00A/P00A_2:7.0/NRD90M/WW_P00A-V5.3.20-20180809:user/release-keys'
LOCK = WORKSPACE / '2026-11-06-asus-recovery-control-transport/evidence/execute.lock'


def main():
    assert hashlib.sha256(BRIDGE.read_bytes()).hexdigest() == BRIDGE_SHA
    assert hashlib.sha256(ADB.read_bytes()).hexdigest() == ADB_SHA
    spec = importlib.util.spec_from_file_location('accepted_readonly_bridge', BRIDGE)
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    deadline = time.monotonic() + 30
    environment = {k: v for k, v in os.environ.items()
                   if not k.startswith(('ADB_', 'ANDROID_ADB_')) and k != 'ANDROID_SERIAL'}
    result = dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  endpoint=ENDPOINT, operation='readonly_stock_health_and_usb_inventory',
                  device_write=False, root_requested=False, physical_presence_assumed=False,
                  qualifies_deployment=False)

    def query(arguments):
        bridge.server_version(deadline)
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError('Stock observation deadline')
        proc = subprocess.run([str(ADB), '-H', '127.0.0.1', '-P', '5037', *arguments],
                              text=True, capture_output=True, timeout=min(12, remaining),
                              env=environment)
        row = dict(exit=proc.returncode, stdout=proc.stdout, stderr=proc.stderr)
        if proc.returncode:
            raise RuntimeError('Stock read-only query failed')
        return row

    try:
        with LOCK.open('r+') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            result['inventory'] = query(['devices', '-l'])
            result['identity'] = query(['-s', ENDPOINT, 'shell', 'getprop', 'ro.build.fingerprint'])
            if result['identity']['stdout'].strip() != FINGERPRINT:
                raise ValueError('Fixed endpoint is not the expected stock firmware')
            for name, arguments in [
                ('enforcing', ['getenforce']),
                ('boot_complete', ['getprop', 'sys.boot_completed']),
                ('secure_adb', ['getprop', 'ro.adb.secure']),
                ('usb_state', ['getprop', 'sys.usb.state']),
                ('battery', ['dumpsys', 'battery']),
                ('memory', ['cat', '/proc/meminfo']),
                ('swap', ['cat', '/proc/swaps']),
                ('low_ram_property', ['getprop', 'ro.config.low_ram']),
                ('heap_growth_limit', ['getprop', 'dalvik.vm.heapgrowthlimit']),
            ]:
                result[name] = query(['-s', ENDPOINT, 'shell', *arguments])
            result['observation_complete'] = True
    except (OSError, RuntimeError, TimeoutError, ValueError, subprocess.TimeoutExpired) as error:
        result.update(observation_complete=False, error_type=type(error).__name__)
    destination = ROOT/'evidence'/('stock-readonly-health-' + str(time.time_ns()) + '.json')
    with destination.open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps(dict(evidence=str(destination), **result), indent=2))
    return 0 if result['observation_complete'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
