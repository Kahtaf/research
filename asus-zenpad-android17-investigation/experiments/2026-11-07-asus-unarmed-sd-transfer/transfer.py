"""Copy inert source files to the owner's prepared SD; no installation controls."""
from pathlib import Path
import datetime
import fcntl
import json
import os
import secrets
import stat
import subprocess

ROOT = Path(__file__).resolve().parent
WORK = ROOT.parent
SOURCE = WORK / '2026-11-07-asus-microsd-install-staging/private/card'
ADB = '/opt/homebrew/Caskroom/android-platform-tools/37.0.1/platform-tools/adb'
SERIAL = 'DEVICE_SERIAL_REDACTED'
BOOT = '6823914c-c2aa-48d1-a5ec-30e7bd925a00'
CARD = '/storage/FA06-080C'
NAMES = ('asus-stock', 'asus-rescue', 'asus-stock-report', 'asus-rescue-report')
ENV = {k: v for k, v in os.environ.items()
       if not k.startswith(('ADB_', 'ANDROID_ADB_')) and k != 'ANDROID_SERIAL'}
state = dict(status='PREPARING', started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
             transport=SERIAL, previous_boot_id=BOOT, controls_copied=False,
             internal_partition_writes=False, copies=[])


def save():
    target = ROOT / 'evidence/transfer.json'
    tmp = target.with_suffix('.tmp')
    with tmp.open('w') as stream:
        json.dump(state, stream, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    tmp.replace(target)


def shell(body):
    token = 'ASUS_SD_COPY_' + secrets.token_hex(16)
    script = ('set -eu\n[ "$(getprop ro.serialno)" = DEVICE_SERIAL_REDACTED ]\n'
              '[ "$(getprop ro.product.device)" = P00A_2 ]\n'
              '[ "$(getprop sys.boot_completed)" = 1 ]\n'
              '[ "$(cat /proc/sys/kernel/random/boot_id)" = ' + BOOT + ' ]\n'
              '[ "$(getenforce)" = Enforcing ]\n'
              '[ "$(cat ' + CARD + '/PROBE.ID)" = dbbb6afb-dd70-4c35-961e-9c977d7164a8 ]\n'
              '[ "$(cat /sys/class/block/mmcblk1/size)" = 31116288 ]\n'
              '[ "$(cat /sys/class/block/mmcblk1/device/type)" = SD ]\n' + body +
              '\nprintf "' + token + '\\n"\n')
    result = subprocess.run([ADB, '-s', SERIAL, 'shell', '-T', '-x', script],
                            env=ENV, capture_output=True, text=True, timeout=20)
    rows = result.stdout.strip().splitlines()
    if result.returncode not in (0, 255) or not rows or rows[-1] != token:
        raise RuntimeError('Device/card guard or shell command failed: ' + result.stderr[:1000])
    return rows[:-1]


def main():
    os.umask(0o077)
    (ROOT / 'evidence').mkdir(exist_ok=True)
    # Exclusive one-shot admission; an interrupted run must be reconciled.
    with (ROOT / 'evidence/started.json').open('x') as stream:
        json.dump(state, stream)
        stream.flush()
        os.fsync(stream.fileno())
    with (WORK / '2026-11-06-asus-recovery-control-transport/evidence/execute.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        files = total = 0
        for path in SOURCE.rglob('*'):
            info = path.lstat()
            if stat.S_ISLNK(info.st_mode):
                raise RuntimeError('Symlink source refused')
            if stat.S_ISREG(info.st_mode):
                if path.name in ('asus-rescue.mode', 'execute.trigger', 'system.trigger',
                                 'boot.trigger', 'manifest.sha256'):
                    raise RuntimeError('Execution control in inert source tree')
                files += 1
                total += info.st_size
        if (files, total) != (5409, 5687439360):
            raise RuntimeError('Staged source inventory changed')
        guards = ''.join('[ ! -e ' + CARD + '/' + name + ' ]\n' for name in NAMES)
        rows = shell(guards + 'df -k ' + CARD + '\n')
        free_kib = int(rows[-1].split()[3])
        if free_kib * 1024 < total + 256 * 1024**2:
            raise RuntimeError('Insufficient card free space')
        state.update(status='COPYING_UNARMED', source_files=files, source_bytes=total)
        save()
        for name in NAMES:
            shell('[ ! -e ' + CARD + '/asus-rescue.mode ]\n')
            state['copies'].append(dict(name=name, status='DISPATCHED'))
            save()
            with (ROOT / 'evidence' / (name + '.log')).open('xb') as log:
                result = subprocess.run([ADB, '-s', SERIAL, 'push', str(SOURCE / name), CARD + '/'],
                                        env=ENV, stdout=log, stderr=subprocess.STDOUT, timeout=1800)
            state['copies'][-1].update(exit=result.returncode,
                                      status='COPY_COMPLETED' if result.returncode == 0 else 'UNKNOWN')
            save()
            if result.returncode:
                raise RuntimeError('ADB source transfer failed; no retry')
        rows = shell('sync\n[ ! -e ' + CARD + '/asus-rescue.mode ]\n'
                     '[ ! -e ' + CARD + '/asus-rescue/execute.trigger ]\n'
                     '[ ! -e ' + CARD + '/asus-stock/system.trigger ]\n'
                     '[ ! -e ' + CARD + '/asus-stock/boot.trigger ]\n'
                     'find ' + CARD + '/asus-stock ' + CARD + '/asus-rescue -type f | wc -l\n')
        if rows != [str(files)]:
            raise RuntimeError('Copied source count mismatch')
        state.update(status='UNARMED_SOURCE_COPY_COMPLETE', device_source_hashes_verified=False,
                     frontend_complete_hash_preflight_still_required=True)
        save()
    print(json.dumps({k: v for k, v in state.items() if k != 'copies'}), flush=True)


if __name__ == '__main__':
    try:
        main()
    except BaseException as error:
        state.update(status='UNKNOWN_OR_INCOMPLETE_NO_RETRY', error=type(error).__name__ + ': ' + str(error))
        save()
        raise
