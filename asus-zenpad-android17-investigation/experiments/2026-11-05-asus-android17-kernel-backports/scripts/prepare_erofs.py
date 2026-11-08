#!/usr/bin/env python3
"""Create a separate feature candidate and apply the pinned EROFS series.

Run on the experiment Linux VM as android. Stops on the first real patch conflict;
never changes the hardware candidate, reference checkout, or tablet.
"""
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

root = Path('/srv/android/asus-android17')
hardware = Path('/srv/android/asus-hardware')
reference = Path('/srv/android/reference-kernel')
expected = 'a668db21f3cfddc5b73f081c6bb532b1b3351b36'
commits = [
    '0977ab3a1693867dd1577aa2a237addc872ac523',
    '3e692e3f9c37c80b20758b9f0eaa237a6cd88818',
    '6e83345c4d69e64cfc43bd3e804567a66bf1e156',
    '87b6a37b6c9ea1f6778145da564d203af7939005',
    '017df3e6cf07653d4400397ada97c659b7e50798',
    'ab07ad8bcedd34d30669f2866f916d07a60623c2',
    '55ceb5aad0ab3e08dd008fff253f0bd80acd299b',
    '230ccf8e8e63fd4bf58a2d4d0f28fff16af7a4b8',
]

def run(args, cwd=None):
    return subprocess.run(args, cwd=cwd, check=True, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE).stdout

assert (hardware/'logs/build-complete').exists(), 'Clean hardware build must finish first'
assert run(['git','rev-parse','HEAD'],reference).decode().strip() == expected
root.mkdir(exist_ok=True)
(root/'patches').mkdir(exist_ok=True)
(root/'logs').mkdir(exist_ok=True)
source = root/'kernel'
if not source.exists():
    shutil.copytree(hardware/'sources/kernel', source)
    run(['git','init'],source)
    run(['git','add','-f','.'],source)
    run(['git','commit','-m','Baseline: pinned MT8163 4.9.337 plus ASUS hardware patches'],source)
    (root/'logs/baseline-commit.txt').write_bytes(run(['git','rev-parse','HEAD'],source))

ledger_path = root/'logs/erofs-import.json'
ledger = json.loads(ledger_path.read_text()) if ledger_path.exists() else []
for i, commit in enumerate(commits):
    if any(row['source_commit']==commit and row['result']=='applied' for row in ledger):
        continue
    patch = root/'patches'/f'{i+1:04d}-{commit[:12]}.patch'
    patch.write_bytes(run(['git','format-patch','-1','--stdout',commit],reference))
    result = subprocess.run(['git','am',str(patch)],cwd=source,capture_output=True,text=True)
    (root/'logs'/f'erofs-{i+1:04d}.log').write_text(result.stdout+result.stderr)
    row = dict(source_commit=commit,patch=str(patch.relative_to(root)),
               sha256=hashlib.sha256(patch.read_bytes()).hexdigest(),
               result='applied' if result.returncode==0 else 'conflict')
    if result.returncode==0:
        row['local_commit']=run(['git','rev-parse','HEAD'],source).decode().strip()
    ledger.append(row)
    ledger_path.write_text(json.dumps(ledger,indent=2)+'\n')
    print(commit, row['result'], flush=True)
    if result.returncode:
        print(result.stdout, result.stderr, flush=True)
        raise SystemExit(result.returncode)
print('EROFS reference series applied; ASUS configuration/build is the next check.')
