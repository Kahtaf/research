"""Two guarded recovery reads; no block writer or reboot path."""
from pathlib import Path
import datetime
import fcntl
import hashlib
import importlib.util
import json
import os
import secrets
import socket
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT.parent
ADB = Path('/opt/homebrew/Caskroom/android-platform-tools/37.0.1/platform-tools/adb')
HELPER = WORK / '2026-11-06-asus-wifi-device-access/scripts/root_shell_wifi.py'
ENGINE = WORK / '2026-11-06-asus-minimal-probe-transition/source/engine.py'
ENDPOINT = 'IP_REDACTED:5555'
SIZE = 16740352

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    os.umask(0o077)
    assert digest(ADB) == '1811e253b21b12cbfda7201ebaf86c10e7ddcb5c606a7a81f7c82b4c429c2d3b'
    assert digest(HELPER) == '684bbe346488dfd0e7dfce741b7547021f019d3749235e6208eb1c9766395f34'
    spec = importlib.util.spec_from_file_location('guarded_recovery', ENGINE)
    engine = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(engine)
    assert engine.BLOCK == '/dev/block/mmcblk0p10' and engine.SIZE == SIZE
    with socket.create_connection(('127.0.0.1', 5037), timeout=2) as server:
        server.sendall(b'000chost:version')
        assert server.recv(64).startswith(b'OKAY'), 'Existing ADB server unavailable'
    env = {k: v for k, v in os.environ.items()
           if not k.startswith(('ADB_', 'ANDROID_ADB_')) and k != 'ANDROID_SERIAL'}
    env['PATH'] = str(ADB.parent) + os.pathsep + env.get('PATH', '/usr/bin:/bin')
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    nonce = secrets.token_hex(8)
    local = ROOT / 'private' / nonce
    local.mkdir(parents=True, mode=0o700)
    remote = '/data/local/tmp/asus-recovery-identity-' + nonce
    calls = []
    def run(argv, body=None, timeout=95):
        result = subprocess.run(argv, input=body, text=True, capture_output=True,
                                timeout=timeout, env=env)
        (local / ('call-' + str(len(calls)) + '.json')).write_text(json.dumps(
            dict(argv=argv, body=body, exit=result.returncode,
                 stdout=result.stdout, stderr=result.stderr), indent=2))
        calls.append(result.returncode)
        if result.returncode:
            raise RuntimeError('Observation command failed; no retry or speculative cleanup')
        return result.stdout.strip()
    def adb(*args):
        return run([str(ADB), '-s', ENDPOINT, *args], timeout=30)
    def root(body):
        return run([sys.executable, '-B', str(HELPER)], engine.DEVICE_GUARD + '\n' + body)
    lock_path = WORK / '2026-11-06-asus-recovery-control-transport/evidence/execute.lock'
    with lock_path.open('r+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        before = adb('shell', 'cat /proc/sys/kernel/random/boot_id')
        body = f'[ ! -e {remote} ]\n[ ! -L {remote} ]\nmkdir {remote}\nchmod 700 {remote}\n'
        for label in ('a', 'b'):
            body += engine.DEVICE_GUARD + f'''
dd if=/dev/block/mmcblk0p10 of={remote}/{label}.bin bs=512 count=32696
[ "$(wc -c < {remote}/{label}.bin)" -eq {SIZE} ]
chown 2000:2000 {remote}/{label}.bin
chmod 600 {remote}/{label}.bin
'''
        root(body + f'chmod 711 {remote}\n')
        rows = []
        for label in ('a', 'b'):
            path = local / (label + '.bin')
            adb('pull', remote + '/' + label + '.bin', str(path))
            assert not path.is_symlink() and path.stat().st_size == SIZE
            rows.append(dict(bytes=SIZE, sha256=digest(path)))
        assert rows[0] == rows[1], 'Recovery changed between independent reads'
        after = adb('shell', 'cat /proc/sys/kernel/random/boot_id')
        assert before == after, 'Stock boot changed during observation'
        cleanup = f'[ ! -L {remote} ]\n[ "$(stat -c \'%u:%g:%a\' {remote})" = 0:0:711 ]\n'
        for label in ('a', 'b'):
            cleanup += f'''[ ! -L {remote}/{label}.bin ]
[ "$(stat -c '%u:%g:%a:%h' {remote}/{label}.bin)" = 2000:2000:600:1 ]
'''
        root(cleanup + f'rm {remote}/a.bin {remote}/b.bin\nrmdir {remote}\n[ ! -e {remote} ]\n')
        assert adb('shell', 'getenforce') == 'Enforcing'
        assert adb('shell', 'getprop sys.boot_completed') == '1'
    record = dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  captures=rows, same_stock_boot=True, boot_id=before,
                  staging_cleanup_verified=True, enforcing=True,
                  block_writes=False, reboot=False, engine_sha256=digest(ENGINE),
                  source_sha256=digest(Path(__file__)))
    evidence = ROOT / 'evidence'
    evidence.mkdir(exist_ok=True)
    with (evidence / 'result.json').open('x') as output:
        json.dump(record, output, indent=2)
        output.write('\n')
    print(json.dumps(record))

if __name__ == '__main__':
    main()
