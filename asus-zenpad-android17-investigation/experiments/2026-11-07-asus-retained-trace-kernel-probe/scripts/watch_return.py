"""Parent read-only observation of a new healthy stock boot over USB or Wi-Fi."""
from pathlib import Path
import datetime
import json
import os
import secrets
import subprocess
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
ADB = '/opt/homebrew/Caskroom/android-platform-tools/37.0.1/platform-tools/adb'
PREVIOUS = '6823914c-c2aa-48d1-a5ec-30e7bd925a00'
TARGETS = ('DEVICE_SERIAL_REDACTED', 'IP_REDACTED:5555')
env = {k: v for k, v in os.environ.items()
       if not k.startswith(('ADB_', 'ANDROID_ADB_')) and k != 'ANDROID_SERIAL'}
started = datetime.datetime.now(datetime.timezone.utc)
receipt = ROOT / 'evidence' / ('return-' + started.strftime('%Y%m%dT%H%M%SZ') + '.json')
state = dict(started_utc=started.isoformat(), previous_boot_id=PREVIOUS,
             read_only=True, reboot=False, saw_unavailable=False)
print(json.dumps(dict(observer_started=True, receipt=str(receipt))), flush=True)
deadline = time.monotonic() + 600
found = False
while time.monotonic() < deadline and not found:
    for target in TARGETS:
        token = 'ASUS_RETURN_' + secrets.token_hex(16) + '=0'
        script = ('set -eu\ngetprop ro.serialno\ngetprop ro.product.device\n'
                  'getprop ro.build.version.sdk\ngetprop sys.boot_completed\n'
                  'cat /proc/sys/kernel/random/boot_id\ngetenforce\n'
                  'getprop ro.adb.secure\nprintf "' + token + '\\n"\n')
        try:
            result = subprocess.run([ADB, '-s', target, 'shell', '-T', '-x', script],
                                    env=env, capture_output=True, text=True, timeout=6)
            rows = result.stdout.strip().splitlines()
            valid = (result.returncode in (0, 255) and len(rows) == 8 and
                     rows[:4] == ['DEVICE_SERIAL_REDACTED', 'P00A_2', '24', '1'] and
                     rows[5:] == ['Enforcing', '1', token] and
                     str(uuid.UUID(rows[4])) == rows[4])
            if valid and rows[4] != PREVIOUS:
                state.update(outcome='new_stock_android_boot_verified',
                             boot_id=rows[4], transport=target)
                found = True
                break
            if not valid:
                state['saw_unavailable'] = True
        except (subprocess.TimeoutExpired, UnicodeError, ValueError):
            state['saw_unavailable'] = True
    if not found:
        time.sleep(3)
if not found:
    state['outcome'] = 'observation_deadline_without_new_stock_boot'
state['ended_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
with receipt.open('x') as stream:
    json.dump(state, stream, indent=2)
    stream.write('\n')
print(json.dumps(state), flush=True)
raise SystemExit(0 if found else 2)
