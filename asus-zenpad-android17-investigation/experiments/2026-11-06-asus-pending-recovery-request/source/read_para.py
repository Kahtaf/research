#!/usr/bin/env python3
"""Fixed read-only whole-p12 captures; no metadata writer or automatic retry."""
from pathlib import Path
import argparse
import datetime
import fcntl
import hashlib
import json
import os
import secrets
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT.parent
HELPER = WORK / '2026-11-06-asus-wifi-device-access/scripts/root_shell_wifi.py'
HELPER_SHA = '684bbe346488dfd0e7dfce741b7547021f019d3749235e6208eb1c9766395f34'
ENDPOINT = 'IP_REDACTED:5555'
EXPECTED = {'before': '8d0cf5c87bcb4abe769f7e4dc2000d45827980b6c12fb792af7bbd0d195c0ef9',
            'after': '8c9e2c158ac95f152d08ea9de929ae36d054131ca4b10620890974ed831480ef'}
GUARD = '''[ -b /dev/block/mmcblk0p12 ]
[ "$(readlink -f /dev/block/mmcblk0p12)" = /dev/block/mmcblk0p12 ]
[ "$(readlink -f /dev/block/platform/mtk-msdc.0/11230000.MSDC0/by-name/para)" = /dev/block/mmcblk0p12 ]
[ "$(cat /sys/class/block/mmcblk0p12/partition)" = 12 ]
[ "$(cat /sys/class/block/mmcblk0p12/start)" = 225576 ]
[ "$(cat /sys/class/block/mmcblk0p12/size)" = 1024 ]
[ "$(cat /sys/class/block/mmcblk0p12/dev)" = 179:12 ]
[ "$(cat /sys/class/block/mmcblk0/queue/logical_block_size)" = 512 ]
asus_node=$(ls -ln /dev/block/mmcblk0p12)
set -- $asus_node
[ "$#" -eq 9 ]
[ "$5" = 179, ]
[ "$6" = 12 ]
[ "$9" = /dev/block/mmcblk0p12 ]'''


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('phase', choices=EXPECTED)
    p.add_argument('--execute', action='store_true')
    args = p.parse_args()
    if sha(HELPER) != HELPER_SHA or HELPER.is_symlink():
        raise RuntimeError('Pinned root helper changed')
    if not args.execute:
        print(json.dumps({'mode': 'PLAN_ONLY', 'phase': args.phase, 'block': '/dev/block/mmcblk0p12',
                          'bytes': 524288, 'copies': 2, 'expected_sha256': EXPECTED[args.phase],
                          'block_writes': False, 'device_contacted': False}, indent=2))
        return 0
    os.umask(0o077)
    private = ROOT / 'private'
    private.mkdir(mode=0o700, exist_ok=True)
    if private.is_symlink():
        raise RuntimeError('Private capture directory is a symlink')
    nonce = secrets.token_hex(8)
    local = private / (args.phase + '-' + nonce)
    local.mkdir(mode=0o700)
    remote = '/data/local/tmp/asus-para-audit-' + nonce
    calls = []

    def run(argv, script=None, timeout=95):
        number = len(calls) + 1
        intent = local / (str(number) + '-intent.json')
        intent.write_text(json.dumps({'argv': argv, 'script': script}, indent=2) + '\n')
        try:
            result = subprocess.run(argv, input=script, capture_output=True, text=True, timeout=timeout)
        except (OSError, UnicodeError, subprocess.TimeoutExpired) as exc:
            (local / (str(number) + '-uncertain.txt')).write_text(str(exc))
            raise RuntimeError('Capture command uncertain; no retry or cleanup') from exc
        calls.append({'argv': argv, 'exit_code': result.returncode})
        (local / (str(number) + '-result.txt')).write_text(result.stdout + result.stderr)
        if result.returncode:
            raise RuntimeError('Capture command failed; preserve evidence without retry')
        return result

    with (WORK / '2026-11-06-asus-recovery-control-transport/evidence/execute.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        body = 'set -eu\n' + GUARD + f'''
[ ! -e {remote} ]
[ ! -L {remote} ]
mkdir {remote}
chmod 700 {remote}
'''
        for name in ('a', 'b'):
            body += GUARD + f'''
dd if=/dev/block/mmcblk0p12 of={remote}/para-{name}.bin bs=512 count=1024
[ "$(wc -c < {remote}/para-{name}.bin)" -eq 524288 ]
chown 2000:2000 {remote}/para-{name}.bin
chmod 600 {remote}/para-{name}.bin
'''
        body += f'chmod 711 {remote}\n'
        run([sys.executable, str(HELPER)], body)
        files = []
        for name in ('a', 'b'):
            path = local / ('para-' + name + '.bin')
            run(['adb', '-s', ENDPOINT, 'pull', remote + '/para-' + name + '.bin', str(path)], timeout=20)
            if path.is_symlink() or path.stat().st_size != 524288:
                raise RuntimeError('Incomplete capture; stop without retry')
            files.append({'path': str(path.relative_to(ROOT)), 'bytes': path.stat().st_size, 'sha256': sha(path)})
        cleanup = f'''set -eu
[ ! -L {remote} ]
[ "$(stat -c '%u:%g:%a' {remote})" = 0:0:711 ]
'''
        for name in ('a', 'b'):
            cleanup += f'''[ ! -L {remote}/para-{name}.bin ]
[ "$(stat -c '%u:%g:%a:%h' {remote}/para-{name}.bin)" = 2000:2000:600:1 ]
'''
        cleanup += f'rm {remote}/para-a.bin {remote}/para-b.bin\nrmdir {remote}\n'
        run([sys.executable, str(HELPER)], cleanup)
    matching = all(item['sha256'] == EXPECTED[args.phase] for item in files)
    result = {'at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'phase': args.phase,
              'files': files, 'both_match_expected': matching, 'staging_cleanup_verified': True,
              'block_writes': False, 'clear_requested': False, 'reboot': False, 'source_sha256': sha(Path(__file__))}
    receipt = ROOT / 'evidence' / (args.phase + '-capture-' + nonce + '.json')
    receipt.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result | {'receipt': str(receipt)}, indent=2))
    return 0 if matching else 2


if __name__ == '__main__':
    raise SystemExit(main())
