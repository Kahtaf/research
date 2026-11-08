#!/usr/bin/env python3
"""Two read-only copies of key/metadata areas; keep private and never upload.

This does not back up userdata and cannot establish a consistent userdata image.
Writes on the tablet are limited to this script's fixed temporary backup files.
"""
from pathlib import Path
import datetime
import hashlib
import json
import os
import subprocess
import sys

os.umask(0o077)
root = Path(__file__).resolve().parents[1]
layout_file = root.parent / '2026-11-05-asus-latest-android-feasibility/evidence/live-partition-layout.json'
layout = {entry['name']: entry for entry in json.loads(layout_file.read_text())}
expected = {'metadata': 33554432, 'kb': 2097152, 'dkb': 2097152, 'frp': 1048576}
for name, size in expected.items():
    assert layout[name]['size_bytes'] == size
tag = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
out = root / 'artifacts/private' / ('encryption-area-backup-' + tag)
out.parent.mkdir(exist_ok=True, mode=0o700)
out.mkdir(mode=0o700)
helper = root / 'scripts/root_shell.py'
adb = ['adb', '-s', 'DEVICE_SERIAL_REDACTED']
temporary = {name: '/data/local/tmp/asus-preserve-' + name + '.bin' for name in expected}

def run_root(script, log):
    with log.open('x') as stream:
        subprocess.run([sys.executable, str(helper)], input=script, text=True,
                       stdout=stream, stderr=stream, timeout=95, check=True)

commands = ['set -eu', 'umask 077']
for name, size in expected.items():
    commands += [
        f'block=$(readlink -f /dev/block/platform/mtk-msdc.0/11230000.MSDC0/by-name/{name})',
        '[ -b "$block" ]',
        'node=${block##*/}',
        f'[ "$(cat /sys/class/block/$node/size)" = {size // 512} ]',
        f'dd if="$block" of={temporary[name]} bs=1048576 count={size // 1048576}',
        f'chmod 600 {temporary[name]}', f'chown 2000:2000 {temporary[name]}',
    ]
commands.append('echo FIXED_AREA_READS_COMPLETE')
for label in ['initial', 'verify']:
    directory = out / label
    directory.mkdir(mode=0o700)
    run_root('\n'.join(commands) + '\n', out / (label + '-root.log'))
    for name, size in expected.items():
        destination = directory / (name + '.bin')
        result = subprocess.run(adb + ['pull', temporary[name], str(destination)],
                                capture_output=True, text=True, timeout=60, check=True)
        destination.chmod(0o600)
        assert destination.stat().st_size == size

report = {'tag': tag, 'scope': 'Two snapshots of four fixed storage areas, not a userdata backup',
          'device_writes': 'Only fixed temporary copies under /data/local/tmp; no raw block writes',
          'areas': []}
for name, size in expected.items():
    first = (out / 'initial' / (name + '.bin')).read_bytes()
    second = (out / 'verify' / (name + '.bin')).read_bytes()
    row = {'name': name, 'bytes': size, 'sha256': hashlib.sha256(first).hexdigest(),
           'second_read_matches': first == second}
    report['areas'].append(row)
report['all_second_reads_match'] = all(row['second_read_matches'] for row in report['areas'])
(out / 'manifest.json').write_text(json.dumps(report, indent=2) + '\n')
run_root('set -eu\nrm -f ' + ' '.join(temporary.values()) + '\n', out / 'cleanup-root.log')
state = subprocess.check_output(adb + ['shell', 'getenforce'], text=True, timeout=10).strip()
assert state == 'Enforcing'
report['final_selinux'] = state
(root / 'evidence/encryption-area-backup-20261106.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'areas': list(expected), 'bytes_per_pass': sum(expected.values()),
                  'all_second_reads_match': report['all_second_reads_match'], 'final_selinux': state}, indent=2))
assert report['all_second_reads_match'], 'Snapshots changed: do not assume a consistent restore set'
