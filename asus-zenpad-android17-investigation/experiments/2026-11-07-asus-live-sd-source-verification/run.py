"""One read-only source observation on the owner's running stock Android."""
from pathlib import Path
import datetime
import fcntl
import hashlib
import json
import os
import secrets
import subprocess
import time
import uuid

ROOT = Path(__file__).resolve().parent
WORK = ROOT.parent
ADB = '/opt/homebrew/Caskroom/android-platform-tools/37.0.1/platform-tools/adb'
ENDPOINT = 'IP_REDACTED:5555'
BOOT = 'c328c9b4-fdaf-4b36-b3e0-5b36c13b3885'
MANIFEST_SHA = '9fe4ec15800257262092f11698525939ebdfb404e150fbc7d308c7f8280ba534'
BINARY_SHA = '0ccbf3521c7acb889ee8f3029155b6f40da664a4abed83bff3fbb8bba95a3e5e'
ENV = {k: v for k, v in os.environ.items()
       if not k.startswith(('ADB_', 'ANDROID_ADB_')) and k != 'ANDROID_SERIAL'}


def save(state):
    target = ROOT / 'evidence/device.json'
    temp = target.with_suffix('.tmp')
    with temp.open('w') as f:
        json.dump(state, f, indent=2)
        f.write('\n')
        f.flush()
        os.fsync(f.fileno())
    temp.replace(target)


def shell(body):
    token = 'ASUS_SOURCE_GUARD_' + secrets.token_hex(16)
    identity = ('test "$(getprop ro.serialno)" = DEVICE_SERIAL_REDACTED\n'
                'test "$(getprop ro.product.device)" = P00A_2\n'
                'test "$(getprop ro.build.version.sdk)" = 24\n'
                'test "$(getprop sys.boot_completed)" = 1\n'
                'test "$(getprop ro.adb.secure)" = 1\n'
                'test "$(getenforce)" = Enforcing\n'
                'test "$(cat /proc/sys/kernel/random/boot_id)" = ' + BOOT + '\n'
                'test "$(cat /storage/FA06-080C/PROBE.ID)" = dbbb6afb-dd70-4c35-961e-9c977d7164a8\n'
                'test "$(cat /sys/class/block/mmcblk1/device/type)" = SD\n'
                'test "$(cat /sys/class/block/mmcblk1/size)" = 31116288\n')
    r = subprocess.run([ADB, '-s', ENDPOINT, 'shell', '-T', '-x',
                        'set -eu\n' + identity + body + '\nprintf "' + token + '\\n"\n'],
                       env=ENV, capture_output=True, text=True, timeout=20)
    if r.returncode not in (0, 255) or not r.stdout.endswith(token + '\n'):
        raise RuntimeError('Stock identity/card/command guard failed: ' + r.stderr[:500])
    return r.stdout[:-len(token)-1]


def adb(args, limit=30):
    r = subprocess.run([ADB, '-s', ENDPOINT, *args], env=ENV,
                       capture_output=True, text=True, timeout=limit)
    if r.returncode:
        raise RuntimeError('ADB staging completion failed: ' + r.stderr[:500])
    return r


def main():
    os.umask(0o077)
    binary = ROOT / 'artifacts/verify-sources.aarch64'
    if hashlib.sha256(binary.read_bytes()).hexdigest() != BINARY_SHA:
        raise RuntimeError('Verifier binary changed')
    source_manifest = WORK / '2026-11-07-asus-microsd-install-staging/private/admitted.manifest'
    content = source_manifest.read_bytes()
    if hashlib.sha256(content).hexdigest() != MANIFEST_SHA:
        raise RuntimeError('Actual parent manifest changed')
    local_manifest = ROOT / 'private/manifest'
    with local_manifest.open('xb') as f:
        f.write(content)
    local_manifest.chmod(0o400)
    run = str(uuid.uuid4())
    stage = '/data/local/tmp/asus-sd-source-verify-' + run
    state = dict(status='PREPARING', run_id=run, boot_id=BOOT, endpoint=ENDPOINT,
                 started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                 stage=stage, manifest_sha256=MANIFEST_SHA, binary_sha256=BINARY_SHA,
                 internal_partition_writes=False, card_writes=False, root_used=False)
    with (ROOT / 'evidence/started.json').open('x') as f:
        json.dump(state, f, indent=2)
    save(state)
    with (WORK / '2026-11-06-asus-recovery-control-transport/evidence/execute.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        shell('test ! -e ' + stage + '\nmkdir -m 700 ' + stage +
              '\ntest "$(stat -c %u:%g:%a ' + stage + ')" = 2000:2000:700\n')
        adb(['push', str(binary), stage + '/verify'])
        adb(['push', str(local_manifest), stage + '/manifest'])
        readback = ROOT / 'private/verifier-readback'
        adb(['pull', stage + '/verify', str(readback)])
        if hashlib.sha256(readback.read_bytes()).hexdigest() != BINARY_SHA:
            raise RuntimeError('Actual staged executable readback differs')
        shell('chmod 700 ' + stage + '/verify\nchmod 400 ' + stage + '/manifest\n'
              'test ! -e /storage/FA06-080C/asus-rescue.mode\n')
        token = 'ASUS_SOURCE_EXIT_' + secrets.token_hex(16)
        command = (stage + '/verify ' + stage + '/manifest &\n'
                   'child=$!\nprintf "%s\\n" "$child" > ' + stage + '/pid\n'
                   'printf "SOURCE_READER_PID=%s\\n" "$child"\n'
                   'wait "$child"\nrc=$?\nprintf "' + token + '=%s\\n" "$rc"\n')
        log = ROOT / 'evidence/device.log'
        state.update(status='READING_CARD', read_deadline_seconds=1800,
                     staged_binary_readback_verified=True)
        save(state)
        started = time.monotonic()
        with log.open('xb', buffering=0) as output:
            child = subprocess.Popen([ADB, '-s', ENDPOINT, 'shell', '-T', '-x', command],
                                     env=ENV, stdout=output, stderr=subprocess.STDOUT)
            state['owned_adb_pid'] = child.pid
            save(state)
            try:
                code = child.wait(timeout=1800)
            except subprocess.TimeoutExpired:
                child.terminate()
                child.wait(timeout=10)
                state.update(status='UNKNOWN_HOST_OBSERVATION_TIMEOUT', target_reader_may_still_run=True,
                             cleanup='not_attempted')
                save(state)
                return 2
        text = log.read_text()
        lines = text.splitlines()
        expected = 'SOURCE_BYTES_VERIFIED files=5409 bytes=5687439360 '
        if (code not in (0, 255) or lines.count(token + '=0') != 1
                or not lines or lines[-1] != token + '=0'
                or sum(line.startswith(expected) for line in lines) != 1):
            state.update(status='FAILED_OR_UNKNOWN_SOURCE_OBSERVATION', host_exit=code,
                         cleanup='not_attempted', elapsed_seconds=time.monotonic()-started)
            save(state)
            print(json.dumps(state), flush=True)
            return 2
        state.update(status='SOURCE_READ_COMPLETED_POSTCHECK_PENDING', reader_exit=0,
                     source_files=5409, source_bytes=5687439360,
                     cleanup='not_yet_verified', elapsed_seconds=time.monotonic()-started)
        save(state)
        try:
            shell('test ! -L ' + stage + '\ntest "$(stat -c %u:%g:%a ' + stage + ')" = 2000:2000:700\n'
                  'rm ' + stage + '/verify ' + stage + '/manifest ' + stage + '/pid\nrmdir ' + stage + '\n')
        except (OSError, RuntimeError, subprocess.SubprocessError) as error:
            state.update(cleanup='unverified_no_retry', cleanup_error=type(error).__name__,
                         ended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
            save(state)
            print(json.dumps(state), flush=True)
            return 2
        state.update(status='ACTUAL_SD_SOURCE_BYTES_VERIFIED', source_files=5409,
                     source_bytes=5687439360, whole_logical_images_rehashed=False,
                     elapsed_seconds=time.monotonic()-started, cleanup='verified',
                     ended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
        save(state)
        print(json.dumps(state), flush=True)
        return 0


if __name__ == '__main__':
    raise SystemExit(main())
