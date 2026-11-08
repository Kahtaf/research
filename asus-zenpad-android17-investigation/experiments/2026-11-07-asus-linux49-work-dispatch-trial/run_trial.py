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
from host_usb import inspect, SERIAL as REPORT_SERIAL, PREFIX

ROOT = Path(__file__).resolve().parent
WORK = ROOT.parent
ADB = '/opt/homebrew/Caskroom/android-platform-tools/37.0.1/platform-tools/adb'
SERIAL = 'DEVICE_SERIAL_REDACTED'
TCP = 'IP_REDACTED:5555'
FULL = '7418c5d3a43c0b458311d880ec87f0d6b781794998d688153f31c3383f7c3752'
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
    fallback = json.loads((ROOT/'evidence/nearby-power.json').read_text())
    assert fallback.get('confirmed') is True or fallback.get('owner_authorized_asynchronous_fallback') is True
    host_baseline = json.loads((ROOT/'evidence/host-baseline.json').read_text())
    assert host_baseline['fresh_identity_absence_verified']
    assert not host_baseline['matching_devices'] and not host_baseline['P49RAM_mounted']
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
                 'normal_android_return_proven': False, 'internal_OS_writes': False,
                 'usb_descriptor_positive': False, 'usb_observations': [], 'usb_inventory_errors': []}
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
        try:
            observed, raw = inspect()
            for node in observed['matching_devices']:
                texts = [v for v in node.values() if isinstance(v, str)]
                products = [v for v in texts if v.startswith(PREFIX)]
                if REPORT_SERIAL in texts and len(products) == 1:
                    state['usb_descriptor_positive'] = True
                    if not state['usb_observations']:
                        state['usb_observations'].append({'at':now(), 'node':node, 'product':products[0]})
                        (ROOT/'private/usb-positive.json').write_text(raw)
                        print(json.dumps({'fresh_PID1_USB_descriptor':True,'product':products[0]}),flush=True)
                    save(receipt,state)
            report = Path('/Volumes/P49RAM/PROBE.TXT')
            if state['usb_descriptor_positive'] and report.is_file() and 'FAT_report' not in state:
                import plistlib, stat
                info = subprocess.run(['diskutil','info','-plist','/Volumes/P49RAM'], capture_output=True, timeout=10, check=True)
                media = plistlib.loads(info.stdout)
                readonly = media.get('MediaReadOnly') is True or media.get('VolumeReadOnly') is True or (media.get('WritableMedia') is False and media.get('WritableVolume') is False)
                fd = os.open(report, os.O_RDONLY | os.O_NOFOLLOW)
                try:
                    st = os.fstat(fd)
                    assert stat.S_ISREG(st.st_mode) and st.st_size <= 4096
                    payload = os.read(fd,4097)
                finally:
                    os.close(fd)
                text = payload.decode('ascii'); pairs = [line.split('=',1) for line in text.splitlines()]
                assert all(len(p)==2 for p in pairs)
                fields = dict(pairs)
                assert len(fields)==7 and list(fields)==['run_id','pid1','sysname','release','version','machine','status']
                assert fields['run_id']=='9342cbf1-3bf0-44d4-b655-a1ca30146a99' and fields['pid1']=='1'
                assert fields['sysname']=='Linux' and fields['machine']=='aarch64' and fields['status']=='pid1_ram_report_ready'
                assert PREFIX+fields['release']==state['usb_observations'][0]['product']
                state['FAT_report']={'at':now(),'fields':fields,'readonly_media_verified':readonly,'accepted':readonly}
                (ROOT/'evidence/PROBE.TXT').write_bytes(payload)
                save(receipt,state)
                print(json.dumps({'FAT_report_observed':True,'readonly_media':readonly,'release':fields['release']}),flush=True)
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, ValueError, OSError, AssertionError) as exc:
            state['usb_inventory_errors'].append({'at':now(),'error':type(exc).__name__+': '+str(exc)[:200]})
        for target in (SERIAL,):
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
    print(json.dumps({'outcome':'PID1_USB_observed_and_stock_returned' if state['usb_descriptor_positive'] else 'stock_returned_without_PID1_USB_observation','usb_descriptor_positive':state['usb_descriptor_positive'],'receipt':str(receipt)}),flush=True)
    return 0  # This RAM-only probe deliberately performs no USB setup; fresh stock return is the host criterion.
if __name__ == '__main__':
    raise SystemExit(main())
