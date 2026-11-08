#!/usr/bin/env python3
"""Export every source change relative to the preceding, preserved hardware spike."""
import difflib
import filecmp
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[1]
before = root.parent / '2026-11-05-asus-mt8163-kernel-bringup/sources/kernel'
after = root / 'sources/kernel'
replay = root / 'evidence/patch-replay'
patch = root / 'patches/0003-asus-power-board-services-legacy-gpu.patch'
def files(directory):
    return {p.relative_to(directory) for p in directory.rglob('*') if p.is_file()}

changed = []
chunks = []
for rel in sorted(files(before) | files(after)):
    a, b = before / rel, after / rel
    if a.is_file() and b.is_file() and filecmp.cmp(a, b, shallow=False):
        continue
    old, new = a.read_bytes() if a.exists() else b'', b.read_bytes() if b.exists() else b''
    if b'\0' in old or b'\0' in new:
        raise ValueError(f'Unexpected binary source change: {rel}')
    chunks.extend(difflib.unified_diff(old.decode('latin1').splitlines(keepends=True),
        new.decode('latin1').splitlines(keepends=True),
        fromfile='a/' + str(rel) if a.exists() else '/dev/null',
        tofile='b/' + str(rel) if b.exists() else '/dev/null'))
    changed.append({'path': str(rel), 'before_sha256': hashlib.sha256(old).hexdigest() if a.exists() else None,
        'sha256': hashlib.sha256(new).hexdigest() if b.exists() else None})
patch.write_bytes(''.join(chunks).encode('latin1'))
replay.mkdir(parents=True, exist_ok=True)
for row in changed:
    a, b = before / row['path'], replay / row['path']
    b.parent.mkdir(parents=True, exist_ok=True)
    if b.exists():
        b.unlink()
    if a.exists():
        shutil.copyfile(a, b)
r = subprocess.run(['patch', '--batch', '--forward', '-p1', '-i', str(patch)],
    cwd=replay, capture_output=True, text=True)
(root / 'evidence/patch-replay.log').write_text(r.stdout + r.stderr)
r.check_returncode()
for row in changed:
    p = replay / row['path']
    actual = hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
    assert actual == row['sha256'], row['path']
(root / 'evidence/patch-manifest.json').write_text(json.dumps({
    'baseline': str(before), 'baseline_commit': 'dc63af1741072236efb511499f1f0b9dd281d694',
    'prerequisites': ['preceding spike patches/0001-build-compatibility.patch', 'preceding spike patches/0002-asus-board-panel-touch.patch'],
    'patch': str(patch.relative_to(root)), 'patch_sha256': hashlib.sha256(patch.read_bytes()).hexdigest(),
    'replay_verified': True, 'files': changed}, indent=2) + '\n')
print(f'{len(changed)} source changes exported and replayed exactly; {patch.stat().st_size} patch bytes')
