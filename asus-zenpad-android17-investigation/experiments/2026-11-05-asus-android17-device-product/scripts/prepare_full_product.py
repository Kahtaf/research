#!/usr/bin/env python3
"""Move the completed module target toward a full system; no device access."""
from pathlib import Path
import datetime
import hashlib
import json
import shutil
import subprocess

ROOT = Path('/srv/android/asus-device-product')
TREE = Path('/srv/android/lineage24')
CANDIDATE = ROOT / 'full-product-candidate/device/asus/p00a'
ACTIVE = TREE / 'device/asus/p00a'
assert (ROOT / 'logs/graphics-build-complete').exists(), 'Finish graphics integration first'
for command in ('soong_ui', 'soong_build', 'ckati'):
    assert subprocess.run(['pgrep', '-x', command], stdout=subprocess.DEVNULL).returncode != 0
backup = ROOT / 'module-target-before-full-product'
assert not backup.exists(), 'Inspect the existing full-product transition before rerunning'
assert not (ACTIVE / '.git').exists(), 'Handle a nested repository explicitly'
link = TREE / 'kernel/asus/p00a-fd'
assert not link.exists() and not link.is_symlink(), 'Reconcile the existing kernel link before deployment'
manifest_path = ROOT / 'full-product-candidate/manifest.json'
manifest = json.loads(manifest_path.read_text())
candidate_root = ROOT / 'full-product-candidate'
expected_paths = {row['path'] for row in manifest['files']}
actual_paths = {str(p.relative_to(candidate_root)) for p in CANDIDATE.rglob('*') if p.is_file()}
assert expected_paths == actual_paths, 'Candidate source set differs from its reviewed manifest'
for row in manifest['files']:
    candidate_file = candidate_root / row['path']
    assert not candidate_file.is_symlink()
    assert candidate_file.stat().st_size == row['bytes'], row['path']
    assert hashlib.sha256(candidate_file.read_bytes()).hexdigest() == row['sha256'], row['path']
kernel = Path('/srv/android/asus-android17/build-main-battery-soc-r1/arch/arm64/boot/Image.gz-dtb')
assert hashlib.sha256(kernel.read_bytes()).hexdigest() == '0d530f1f59bb0a87a18f4ced4fb241845e916baa16676675e6af80e2bd0f5acf'
source = Path('/srv/android/asus-android17/kernel-bpf-fd')
assert subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip() == '717bb3c9e13ce573cfdd2dda856debd27a0fa17f'
shutil.copytree(ACTIVE, backup, symlinks=True)
for path in CANDIDATE.rglob('*'):
    if path.is_file():
        output = ACTIVE / path.relative_to(CANDIDATE)
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, output)
(ACTIVE / 'prebuilt').mkdir(exist_ok=True)
shutil.copyfile(kernel, ACTIVE / 'prebuilt/Image.gz-dtb')
link.symlink_to(source, target_is_directory=True)
record = dict(time=datetime.datetime.now(datetime.timezone.utc).isoformat(),
              previous_product_backup=str(backup), kernel_source=str(source),
              kernel_sha256=hashlib.sha256(kernel.read_bytes()).hexdigest(),
              candidate_revision=manifest['revision'],
              candidate_manifest_sha256=hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
              status='full product deployed for variable checks and compilation; no images flashed')
(ROOT / 'logs/full-product-deployed.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps(record, indent=2))
