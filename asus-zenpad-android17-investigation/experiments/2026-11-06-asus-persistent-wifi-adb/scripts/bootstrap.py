"""One exact-device USB bootstrap, then authenticated persistent Wi-Fi ADB."""
from pathlib import Path
import datetime
import fcntl
import hashlib
import json
import os
import re
import socket
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT.parent
ADB = Path('/opt/homebrew/Caskroom/android-platform-tools/37.0.1/platform-tools/adb')
HELPER = WORK / '2026-11-06-asus-wifi-device-access/scripts/root_shell_wifi.py'
SERIAL = 'DEVICE_SERIAL_REDACTED'
ENDPOINT = 'IP_REDACTED:5555'
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    os.umask(0o077)
    assert sha(ADB) == '1811e253b21b12cbfda7201ebaf86c10e7ddcb5c606a7a81f7c82b4c429c2d3b'
    assert sha(HELPER) == '684bbe346488dfd0e7dfce741b7547021f019d3749235e6208eb1c9766395f34'
    attempt = str(uuid.uuid4())
    private = ROOT / 'private' / attempt
    private.mkdir(parents=True, mode=0o700)
    (ROOT / 'evidence').mkdir(exist_ok=True)
    env = {k: v for k, v in os.environ.items()
           if not k.startswith(('ADB_', 'ANDROID_ADB_')) and k != 'ANDROID_SERIAL'}
    env['PATH'] = str(ADB.parent) + os.pathsep + env.get('PATH', '/usr/bin:/bin')
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    record = dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  wifi_connected=False, persistence_enabled=False, image_writes=False)
    count = 0
    def run(args, body=None, timeout=12):
        nonlocal count
        count += 1
        result = subprocess.run(args, input=body, text=True, capture_output=True,
                                timeout=timeout, env=env)
        (private / ('command-' + str(count) + '.json')).write_text(json.dumps(dict(
            argv=args, exit=result.returncode, stdout=result.stdout,
            stderr=result.stderr), indent=2) + '\n')
        if result.returncode:
            raise RuntimeError('ADB operation did not complete successfully')
        return result.stdout.strip()
    try:
        with socket.create_connection(('127.0.0.1', 5037), timeout=2) as server:
            server.sendall(b'000chost:version')
            assert server.recv(64).startswith(b'OKAY'), 'Existing ADB server unavailable'
        run([str(ADB), '-s', SERIAL, 'wait-for-usb-device'], timeout=300)
        expected = ['DEVICE_SERIAL_REDACTED', 'P00A_2', '24', '1', '1', 'Enforcing']
        query = ('getprop ro.serialno; getprop ro.product.device; getprop ro.build.version.sdk; '
                 'getprop ro.adb.secure; getprop sys.boot_completed; getenforce')
        assert run([str(ADB), '-s', SERIAL, 'shell', query]).splitlines() == expected
        address = run([str(ADB), '-s', SERIAL, 'shell', 'ip -f inet addr show wlan0'])
        assert re.search(r'\binet 192\.168\.68\.63/', address), 'Wi-Fi address changed; do not retarget blindly'
        lock_path = WORK / '2026-11-06-asus-recovery-control-transport/evidence/execute.lock'
        with lock_path.open('r+') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            run([str(ADB), '-s', SERIAL, 'tcpip', '5555'])
            connected = run([str(ADB), 'connect', ENDPOINT])
            assert 'connected to ' + ENDPOINT in connected, 'TCP endpoint did not connect'
            assert run([str(ADB), '-s', ENDPOINT, 'shell', query]).splitlines() == expected
            record['wifi_connected'] = True
            run([sys.executable, '-B', str(HELPER)], body=(
                'setprop persist.adb.tcp.port 5555\n'
                '[ "$(getprop persist.adb.tcp.port)" = 5555 ]\n'
                '[ "$(getprop ro.adb.secure)" = 1 ]\n'), timeout=95)
            assert run([str(ADB), '-s', ENDPOINT, 'shell',
                        'getprop persist.adb.tcp.port; getprop ro.adb.secure; getenforce']).splitlines() == ['5555', '1', 'Enforcing']
            record.update(persistence_enabled=True, secure_adb=True, enforcing=True,
                          endpoint=ENDPOINT)
    except (OSError, AssertionError, RuntimeError, subprocess.TimeoutExpired) as error:
        record.update(error_type=type(error).__name__, error=str(error), automatic_retry=False)
    record['attempt'] = attempt
    with (ROOT / 'evidence' / ('result-' + attempt + '.json')).open('x') as output:
        json.dump(record, output, indent=2)
        output.write('\n')
    print(json.dumps(record), flush=True)
    return 0 if record['wifi_connected'] and record['persistence_enabled'] else 2

if __name__ == '__main__':
    raise SystemExit(main())
