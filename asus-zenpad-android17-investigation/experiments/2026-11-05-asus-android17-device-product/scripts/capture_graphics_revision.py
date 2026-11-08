#!/usr/bin/env python3
"""Checkpoint strict core ELF stamps, installed graphics, and build provenance."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tarfile

ROOT = Path('/srv/android/asus-device-product')
TREE = Path('/srv/android/lineage24')
parser = argparse.ArgumentParser()
parser.add_argument('--revision', required=True)
args = parser.parse_args()
assert re.fullmatch(r'r[0-9]+', args.revision)
OUT = ROOT / ('graphics-result-' + args.revision)
assert not OUT.exists()
OUT.mkdir()
source = TREE / 'vendor/asus/p00a'
inputs = json.loads((source / 'input-manifest.json').read_text())
manifest = []
def save(path, relative):
    dest = OUT / relative
    dest.parent.mkdir(parents=True, exist_ok=True)
    assert path.is_file(), path
    shutil.copyfile(path, dest)
    manifest.append(dict(path=str(relative), source=str(path), bytes=path.stat().st_size,
                         sha256=hashlib.sha256(dest.read_bytes()).hexdigest()))
checks = []
for item in inputs:
    rel = Path(item['path']).relative_to('proprietary')
    save(TREE / 'out/target/product/p00a/system' / rel, Path('system') / rel)
    name = 'p00a_legacy_' + rel.name.removesuffix('.so').replace('.', '_').replace('-', '_').replace('+', 'x')
    arch = 'android_arm64_armv8-a_shared' if rel.parts[0] == 'lib64' else 'android_arm_armv8-a_cortex-a53_shared'
    stamp = TREE / 'out/soong/.intermediates/vendor/asus/p00a' / name / arch / (rel.name + '.check_elf_file')
    assert stamp.is_file(), f'Missing strict core ELF check: {stamp}'
    checks.append(dict(source=item['path'], stamp=str(stamp), mtime=stamp.stat().st_mtime))
for directory in ['lib', 'lib64']:
    save(TREE / 'out/target/product/p00a/system' / directory / 'libp00a_legacy_memory.so',
         Path('system') / directory / 'libp00a_legacy_memory.so')
    symlink = TREE / 'out/target/product/p00a/system/vendor' / directory / 'egl/libGLES_mali.so'
    assert symlink.is_symlink(), symlink
    assert str(symlink.readlink()) == f'/system/{directory}/egl/libGLES_mali.so'
services = ['android.hardware.graphics.composer@2.1-service', 'android.hardware.graphics.allocator@2.0-service']
for name in services:
    rel = Path('system/vendor/bin/hw') / name
    save(TREE / 'out/target/product/p00a' / rel, rel)
for name in ['ACCOUNT_REDACTED', 'ACCOUNT_REDACTED']:
    for directory in ['lib', 'lib64']:
        rel = Path('system/vendor') / directory / 'hw' / name
        p = TREE / 'out/target/product/p00a' / rel
        if p.exists():
            save(p, rel)
for rel in ['system/bin/linkerconfig']:
    save(TREE / 'out/target/product/p00a' / rel, Path(rel))
for p in source.glob('*.json'):
    save(p, Path('inputs') / p.name)
for rel in ['device/asus/p00a/device.mk', 'device/asus/p00a/lights/Android.bp', 'vendor/asus/p00a/Android.bp']:
    save(TREE / rel, Path('source') / rel)
projects = {}
for project in ['bionic','system/linkerconfig','system/memory/libion','frameworks/native','hardware/interfaces']:
    projects[project] = subprocess.check_output(['git','rev-parse','HEAD'], cwd=TREE/project, text=True).strip()
(OUT / 'strict-checks.json').write_text(json.dumps(checks, indent=2)+'\n')
(OUT / 'source-pins.json').write_text(json.dumps(projects, indent=2)+'\n')
(OUT / 'manifest.json').write_text(json.dumps(dict(revision=args.revision,
    captured_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    strict_elf_checks=len(checks), files=manifest), indent=2)+'\n')
with tarfile.open(ROOT / ('graphics-result-' + args.revision + '.tar.gz'), 'w:gz') as archive:
    archive.add(OUT, arcname=OUT.name)
print(f'Captured {len(manifest)} files and {len(checks)} strict core ELF checks at {OUT}')
