#!/usr/bin/env python3
"""Run only pinned mtkclient gettargetconfig, skipping watchdog initialization."""
import json
import argparse
import datetime
import re
import os
import signal
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
def valid_tag(value):
    if not re.fullmatch(r'[A-Za-z0-9_-]+', value):
        raise argparse.ArgumentTypeError('Use letters, digits, underscores or hyphens only')
    return value

parser.add_argument('--tag', type=valid_tag,
                    default=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
tag = parser.parse_args().tag
repo = root / 'sources/mtkclient'
pin = '118a000a83ea31c4f427fe5225abfe964546e05e'
if subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip() != pin:
    raise SystemExit('Unexpected upstream source revision')
expected_patch = (root / 'patches/0001-explicit-usb-id-dict-compat.patch').read_bytes()
actual_patch = subprocess.check_output(['git', '-C', str(repo), 'diff', '--binary', '--'])
if actual_patch != expected_patch:
    raise SystemExit('Unexpected upstream source modifications')
os.umask(0o077)
logpath = root / f'evidence/upstream-native-config-{tag}-raw.log'
args = [sys.executable, '-u', str(repo / 'mtk.py'), 'gettargetconfig',
        '--skipwdt', '--vid', '0x0e8d', '--pid', '0x2000', '--debugmode']
with logpath.open('x') as log:
    process = subprocess.Popen(args, cwd=root, stdin=subprocess.DEVNULL,
                               stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    try:
        code = process.wait(timeout=70)
        result = dict(returncode=code, timeout=False)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
        result = dict(returncode=process.returncode, timeout=True)
result.update(command=args, source_pin=pin, log=str(logpath),
              intent='Read configuration only; watchdog init skipped; no payload, DA, write, unlock or erase command')
(root / f'evidence/upstream-native-config-{tag}-process.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result))
