#!/usr/bin/env python3
"""Supervise one revision without shell pipelines losing the build exit status."""
import argparse
import datetime
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path('/srv/android/asus-device-product')
parser = argparse.ArgumentParser()
parser.add_argument('--revision', required=True)
args = parser.parse_args()
r = args.revision
assert re.fullmatch(r'r[0-9]+', r)
job = ROOT / f'logs/graphics-build-{r}-job.json'
log = ROOT / f'logs/graphics-build-{r}.log'
assert not job.exists() and not log.exists(), 'Never overwrite or restart a recorded build'
assert json.loads((ROOT / f'logs/graphics-deploy-{r}.json').read_text())['exit_status'] == 0
state = dict(revision=r, supervisor_pid=os.getpid(), log=str(log),
             started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
with log.open('x') as stream:
    child = subprocess.Popen(['bash', str(Path(__file__).with_name('build_graphics.sh')), r], stdout=stream, stderr=subprocess.STDOUT)
    state.update(build_pid=child.pid, status='running')
    job.write_text(json.dumps(state, indent=2)+'\n')
    result = child.wait()
state.update(exit_status=result, status='completed' if result == 0 else 'failed',
             ended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
job.write_text(json.dumps(state, indent=2)+'\n')
raise SystemExit(result)
