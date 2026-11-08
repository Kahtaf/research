"""One recovery entry after verified installation, then bounded stock-return observation."""
from pathlib import Path
import argparse
import datetime
import fcntl
import json
import os
import secrets
import subprocess
import time
import uuid

ROOT = Path(__file__).resolve().parent
WORK = ROOT.parent
ADB = '/opt/homebrew/Caskroom/android-platform-tools/37.0.1/platform-tools/adb'
SERIAL = 'DEVICE_SERIAL_REDACTED'
TCP = 'IP_REDACTED:5555'
FULL = '4fb2f280ba90e9e1487b3728056a67ccd4883f918cc81a1145c100a3eb999a26'
ENV = {k: v for k, v in os.environ.items()
       if not k.startswith(('ADB_', 'ANDROID_ADB_')) and k != 'ANDROID_SERIAL'}
def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(path, value):
    temp = path.with_suffix('.tmp')
    with temp.open('w') as f:
        json.dump(value, f, indent=2)
        f.write('\n')
        f.flush()
        os.fsync(f.fileno())
    temp.replace(path)
    fd = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)
def query(target):
    token = 'ASUS_RETURN_'+secrets.token_hex(16)+'=0'
    body = ('set -eu\ngetprop ro.serialno\ngetprop ro.product.device\n'
            'getprop ro.build.version.sdk\ngetprop sys.boot_completed\n'
            'cat /proc/sys/kernel/random/boot_id\ngetenforce\n'
            'getprop ro.adb.secure\nprintf "'+token+'\\n"\n')
    q = subprocess.run([ADB, '-s', target, 'shell', '-T', '-x', body],
                       env=ENV, capture_output=True, text=True, timeout=5)
    rows = q.stdout.strip().splitlines()
    if (q.returncode not in (0, 255) or len(rows) != 8 or
        rows[:4] != [SERIAL, 'P00A_2', '24', '1'] or
        rows[5:] != ['Enforcing', '1', token]):
        return None
    return rows[4] if str(uuid.UUID(rows[4])) == rows[4] else None
def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--install-receipt', type=Path, required=True)
    p.add_argument('--execute', action='store_true')
    args = p.parse_args()
    if not args.execute:
        print(json.dumps({'mode': 'PLAN_ONLY', 'reboot': False}))
        return 0
    os.umask(0o077)
    install = json.loads(args.install_receipt.read_text())
    assert install['outcome'] in ('installed_full_hash_verified', 'verified_already_candidate')
    assert install['cleanup'] == 'verified' and install['full_p10_sha256'] == FULL
    baseline = json.loads((ROOT/'evidence/physical-baseline.json').read_text())
    receipt = ROOT/'evidence/recovery-entry.json'
    assert not receipt.exists(), 'Entry already attempted: inspect, never resend automatically'
    lockpath = WORK/'2026-11-06-asus-recovery-control-transport/evidence/execute.lock'
    with lockpath.open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        previous = query(SERIAL)
        assert previous == baseline['boot_id'], 'Fresh original stock boot required'
        state = {'started_utc': now(), 'previous_boot_id': previous,
                 'candidate_p10_sha256': FULL, 'install_receipt': str(args.install_receipt.resolve()),
                 'transport': 'USB', 'reboot_requests': 1, 'dispatch': 'DISPATCHING',
                 'normal_android_return_proven': False, 'internal_OS_writes': False}
        save(receipt, state)
        try:
            q = subprocess.run([ADB, '-s', SERIAL, 'reboot', 'recovery'],
                               env=ENV, capture_output=True, text=True, timeout=12)
            state.update(dispatch='ACKNOWLEDGED' if q.returncode == 0 else 'UNKNOWN',
                         command_exit=q.returncode, stdout=q.stdout[:500], stderr=q.stderr[:500])
        except (subprocess.TimeoutExpired, UnicodeError) as exc:
            state.update(dispatch='UNKNOWN', error=type(exc).__name__)
        state['dispatch_finished_utc'] = now()
        save(receipt, state)
    print(json.dumps({'dispatch': state['dispatch'], 'previous_boot_id': previous,
                      'receipt': str(receipt)}), flush=True)
    deadline = time.monotonic()+300
    reconnect_at = time.monotonic()+45
    found = None
    while time.monotonic() < deadline and not found:
        for target in (SERIAL, TCP):
            try:
                current = query(target)
            except (subprocess.TimeoutExpired, UnicodeError, ValueError):
                current = None
            if current and current != previous:
                found = current
                state.update(normal_android_return_proven=True, new_stock_boot_id=current,
                             return_transport=target, observed_utc=now())
                break
        if not found and time.monotonic() >= reconnect_at:
            for op in ('disconnect', 'connect'):
                try:
                    subprocess.run([ADB, op, TCP], env=ENV, capture_output=True, timeout=8)
                except subprocess.TimeoutExpired:
                    pass
            reconnect_at = time.monotonic()+30
        if not found:
            time.sleep(3)
    state['observation_finished_utc'] = now()
    save(receipt, state)
    if not found:
        print(json.dumps({'outcome': 'no_verified_stock_return_at_deadline', 'receipt': str(receipt)}))
        return 2
    print(json.dumps({'outcome': 'new_stock_android_verified', 'boot_id': found,
                      'transport': state['return_transport']}), flush=True)
    # Only reconnect the host's stale TCP endpoint; never restart adbd/server.
    for op in ('disconnect', 'connect'):
        subprocess.run([ADB, op, TCP], env=ENV, capture_output=True, timeout=10)
    collector = WORK/'2026-11-06-asus-android17-orchestration/scripts/collect_trace_v2.py'
    q = subprocess.run(['python3', '-B', str(collector), '--boot-id', found,
                        '--trial-receipt', str(receipt)], env=ENV,
                       capture_output=True, text=True, timeout=120)
    (ROOT/'evidence/collector.stdout').write_text(q.stdout)
    (ROOT/'evidence/collector.stderr').write_text(q.stderr)
    print(q.stdout, end='', flush=True)
    if q.stderr:
        print(q.stderr, end='', flush=True)
    return q.returncode
if __name__ == '__main__':
    raise SystemExit(main())
