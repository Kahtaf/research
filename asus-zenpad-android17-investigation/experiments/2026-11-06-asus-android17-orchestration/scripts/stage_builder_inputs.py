#!/usr/bin/env python3
"""Builder-only staging of pinned full-product and Google source inputs."""
from pathlib import Path
import hashlib
import json
import subprocess
import tarfile
import urllib.request

ROOT = Path('/srv/android/asus-device-product')
assert ROOT.is_dir()

def unpack(name, expected, destination):
    archive = ROOT / name
    assert hashlib.sha256(archive.read_bytes()).hexdigest() == expected, name
    assert not destination.exists(), destination
    destination.mkdir()
    with tarfile.open(archive) as stream:
        for member in stream.getmembers():
            path = Path(member.name)
            assert not path.is_absolute() and '..' not in path.parts
            assert member.isfile() or member.isdir(), member.name
        stream.extractall(destination, filter='data')

candidate = ROOT / 'full-product-candidate'
previous = ROOT / 'full-product-candidate-before-r4'
assert not previous.exists()
assert not (ROOT / 'logs/full-product-deployed.json').exists()
if candidate.exists():
    candidate.rename(previous)
unpack('full-product-inputs-r4.tar.gz',
       '66fa9e5cff2d90f936a22766593374948a99999baa82ec19c0b8707ccc8ea28c', candidate)
google = ROOT / 'google-inline'
unpack('google-inline-inputs.tar.gz',
       'a08b51a63d5e79b83aa3d579682d98ec538a0087d433954019f30795c0decfb6', google)
name = 'MindTheGapps-17.0.0-arm64-20261022_132445.zip'
destination = google / name
url = 'https://github.com/MindTheGapps/17.0.0-arm64/releases/download/' + name[:-4] + '/' + name
temporary = destination.with_suffix('.zip.part')
digest = hashlib.sha256()
size = 0
with urllib.request.urlopen(url, timeout=60) as response, temporary.open('xb') as output:
    while block := response.read(1024 * 1024):
        size += len(block)
        assert size <= 544284463
        digest.update(block)
        output.write(block)
assert size == 544284463
assert digest.hexdigest() == 'a6844eeb2613541558237e467b20feb01f8b45b2ebab0109834140ea59b6ca4d'
temporary.rename(destination)
subprocess.run(['python3', str(google / 'scripts/stage_inline.py'), 'stage',
                '--zip', str(destination), '--manifest', str(google / 'evidence/inline-source-manifest.json'),
                '--android-root', '/srv/android/lineage24'], check=True)
subprocess.run(['python3', str(google / 'scripts/stage_inline.py'), 'check',
                '--android-root', '/srv/android/lineage24'], check=True)
subprocess.run(['python3', str(ROOT / 'prepare_full_product.py')], check=True)
print(json.dumps({'staged': True, 'google_zip_sha256': digest.hexdigest(),
                  'full_build_started': False}), flush=True)
