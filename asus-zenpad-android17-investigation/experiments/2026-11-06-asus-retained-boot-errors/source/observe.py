"""Read bounded public kernel diagnostic paths; retain raw output privately."""
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

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT.parent
ADB = Path('/opt/homebrew/Caskroom/android-platform-tools/37.0.1/platform-tools/adb')
HELPER = WORK / '2026-11-06-asus-wifi-device-access/scripts/root_shell_wifi.py'
PATHS = ('/proc/last_kmsg', '/sys/fs/pstore/console-ramoops',
         '/sys/fs/pstore/console-ramoops-0', '/sys/fs/pstore/dmesg-ramoops-0',
         '/proc/aed/current-ke-console', '/proc/aed/previous-ke-console')

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    os.umask(0o077)
    assert sha(ADB) == '1811e253b21b12cbfda7201ebaf86c10e7ddcb5c606a7a81f7c82b4c429c2d3b'
    assert sha(HELPER) == '684bbe346488dfd0e7dfce741b7547021f019d3749235e6208eb1c9766395f34'
    with socket.create_connection(('127.0.0.1', 5037), timeout=2) as stream:
        stream.sendall(b'000chost:version')
        assert stream.recv(64).startswith(b'OKAY')
    env = {k: v for k, v in os.environ.items()
           if not k.startswith(('ADB_', 'ANDROID_ADB_')) and k != 'ANDROID_SERIAL'}
    env['PATH'] = str(ADB.parent) + os.pathsep + env.get('PATH', '/usr/bin:/bin')
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    private = ROOT / 'private'
    private.mkdir(mode=0o700)
    body = '[ "$(getprop sys.boot_completed)" = 1 ]\ncommand -v od >/dev/null\n'
    for number, path in enumerate(PATHS):
        body += f'''if [ -r {path} ]; then
printf '\\nBOOT_LOG_BEGIN_{number}\\n'
od -An -v -tx1 -N262144 {path}
printf '\\nBOOT_LOG_END_{number}\\n'
else
printf '\\nBOOT_LOG_UNAVAILABLE_{number}\\n'
fi
'''
    lock_path = WORK / '2026-11-06-asus-recovery-control-transport/evidence/execute.lock'
    with lock_path.open('r+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        result = subprocess.run([sys.executable, '-B', str(HELPER)], input=body,
                                capture_output=True, text=True, timeout=95, env=env)
        (private / 'command.json').write_text(json.dumps(dict(
            body=body, exit=result.returncode, stdout=result.stdout,
            stderr=result.stderr), indent=2))
        if result.returncode:
            raise RuntimeError('Read-only diagnostic failed; stop without retry')
    observations = []
    for number, path in enumerate(PATHS):
        match = re.findall(r'^BOOT_LOG_BEGIN_' + str(number) + r'\r?\n(.*?)^BOOT_LOG_END_' +
                           str(number) + r'\r?$', result.stdout, re.M | re.S)
        absent = re.findall(r'^BOOT_LOG_UNAVAILABLE_' + str(number) + r'\r?$', result.stdout, re.M)
        assert (len(match), len(absent)) in ((1, 0), (0, 1)), 'Ambiguous diagnostic framing'
        row = dict(path=path, available=bool(match), bounded_bytes=0, selected_events=[])
        if match:
            assert re.fullmatch(r'[0-9a-f\s]*', match[0])
            data = bytes.fromhex(match[0])
            assert len(data) <= 262144
            row['bounded_bytes'] = len(data)
            row['captured_sha256'] = hashlib.sha256(data).hexdigest()
            (private / ('log-' + str(number) + '.bin')).write_bytes(data)
            for line in data.decode('utf-8', 'replace').splitlines():
                if re.search(r'Initramfs unpacking failed|RAMDISK:.*(?:error|invalid|incomplete)|'
                             r'Failed to execute /init|Kernel panic - not syncing: No working init found|'
                             r'Failed to write descriptors to .*usb-ffs|coldboot.*timed out', line, re.I):
                    line = re.sub(r'\b(?:0x)?[0-9a-fA-F]{8,}\b', '<hex>', line)
                    row['selected_events'].append(line[:240])
            row['selected_events'] = row['selected_events'][:20]
        observations.append(row)
    record = dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  observations=observations, max_bytes_per_path=262144,
                  specific_recovery_attempt_attribution=False, block_reads=False,
                  block_writes=False, reboot=False, source_sha256=sha(Path(__file__)))
    evidence = ROOT / 'evidence'
    evidence.mkdir()
    with (evidence / 'result.json').open('x') as output:
        json.dump(record, output, indent=2)
        output.write('\n')
    print(json.dumps(record))

if __name__ == '__main__':
    main()
