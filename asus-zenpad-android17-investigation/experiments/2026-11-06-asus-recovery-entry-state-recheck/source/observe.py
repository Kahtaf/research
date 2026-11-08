"""Use the established two-capture host hash reader; never clear a request."""
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import os
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
READER = WORKSPACE / '2026-11-06-asus-pending-recovery-request/source/read_para.py'
READER_SHA = 'b8b0abf17c9f9909234bb03cf1a9e2295218857d02071813e3feaeb6937d1d6b'
ADB = Path('/opt/homebrew/Caskroom/android-platform-tools/37.0.1/platform-tools/adb')
ADB_SHA = '1811e253b21b12cbfda7201ebaf86c10e7ddcb5c606a7a81f7c82b4c429c2d3b'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--observe', action='store_true')
    args = parser.parse_args()
    if not args.observe:
        print(json.dumps(dict(mode='PLAN_ONLY', reads=2, bytes_each=524288,
                              hashing='host', partition_write=False,
                              clear_requested=False, reboot=False, device_contacted=False)))
        return 0
    for path, pin in ((READER, READER_SHA), (ADB, ADB_SHA)):
        if path.is_symlink() or not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != pin:
            raise ValueError('Pinned local dependency changed')
    os.umask(0o077)
    environment = {key: value for key, value in os.environ.items()
                   if not key.startswith(('ADB_', 'ANDROID_ADB_')) and key != 'ANDROID_SERIAL'}
    environment['PATH'] = str(ADB.parent) + os.pathsep + environment.get('PATH', '/usr/bin:/bin')
    record = dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  reader_sha256=READER_SHA, outcome='UNKNOWN', partition_write=False,
                  clear_requested=False, reboot=False, retry=False)
    try:
        # The pinned reader owns the shared device lock, guarded root capture,
        # private local files, host hashes, and bounded exact staging cleanup.
        proc = subprocess.run([sys.executable, '-B', str(READER), 'after', '--execute'],
                              capture_output=True, text=True, timeout=220, env=environment)
        record.update(exit=proc.returncode, stdout=proc.stdout, stderr=proc.stderr)
        if proc.returncode == 0:
            result = json.loads(proc.stdout)
            if result.get('both_match_expected') is True and result.get('staging_cleanup_verified') is True:
                record['outcome'] = 'CLEAR_STATE_OBSERVED'
    except (OSError, UnicodeError, ValueError, subprocess.TimeoutExpired) as error:
        record['error_type'] = type(error).__name__
    destination = ROOT / 'evidence' / ('host-reader-' + str(time.time_ns()) + '.json')
    with destination.open('x') as stream:
        json.dump(record, stream, indent=2)
        stream.write('\n')
    print(json.dumps(dict(receipt=str(destination), outcome=record['outcome'])))
    return 0 if record['outcome'] == 'CLEAR_STATE_OBSERVED' else 1


if __name__ == '__main__':
    raise SystemExit(main())
