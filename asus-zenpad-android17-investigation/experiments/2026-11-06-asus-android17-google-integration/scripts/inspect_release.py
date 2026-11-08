#!/usr/bin/env python3
"""Fetch pinned upstream release, verify digest and inspect without executing it."""
import datetime
import hashlib
import json
from pathlib import Path
import shutil
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
TAG = 'MindTheGapps-17.0.0-arm64-20261022_132445'
NAME = TAG + '.zip'
SIZE = 544284463
SHA = 'a6844eeb2613541558237e467b20feb01f8b45b2ebab0109834140ea59b6ca4d'
API = 'https://api.github.com/repos/MindTheGapps/17.0.0-arm64/releases/tags/' + TAG


def download(url, destination):
    temporary = destination.with_suffix(destination.suffix + '.partial')
    if temporary.exists():
        raise RuntimeError('Inspect existing partial before retrying')
    digest = hashlib.sha256()
    length = 0
    request = urllib.request.Request(url, headers={'User-Agent': 'asus-android17-port'})
    try:
        with urllib.request.urlopen(request, timeout=45) as response, temporary.open('xb') as out:
            while chunk := response.read(1024 * 1024):
                out.write(chunk)
                digest.update(chunk)
                length += len(chunk)
                if length > SIZE:
                    raise ValueError('Release exceeds pinned size')
        if length != SIZE or digest.hexdigest() != SHA:
            raise ValueError('Release size or digest mismatch')
        temporary.rename(destination)
    except BaseException:
        # Preserve incomplete evidence; do not mistake it for the verified file.
        raise


def main():
    (ROOT / 'evidence').mkdir(exist_ok=True)
    (ROOT / 'downloads').mkdir(exist_ok=True)
    request = urllib.request.Request(API, headers={'User-Agent': 'asus-android17-port'})
    with urllib.request.urlopen(request, timeout=30) as response:
        release = json.load(response)
    asset = next(a for a in release['assets'] if a['name'] == NAME)
    if asset['size'] != SIZE or asset.get('digest') != 'sha256:' + SHA:
        raise ValueError('Upstream metadata differs from pinned release')
    (ROOT / 'evidence/release.json').write_text(json.dumps(release, indent=2) + '\n')
    package = ROOT / 'downloads' / NAME
    if not package.exists():
        if shutil.disk_usage(ROOT).free < SIZE + 1024 ** 3:
            raise RuntimeError('Need package size plus 1 GiB remaining free')
        download(asset['browser_download_url'], package)
    digest = hashlib.sha256()
    with package.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    if package.stat().st_size != SIZE or digest.hexdigest() != SHA:
        raise ValueError('Existing package does not match pinned digest')
    with zipfile.ZipFile(package) as archive:
        members = [dict(path=i.filename, bytes=i.file_size, compressed_bytes=i.compress_size)
                   for i in archive.infolist() if not i.is_dir()]
        groups = {}
        for item in members:
            prefix = item['path'].split('/', 1)[0]
            groups[prefix] = groups.get(prefix, 0) + item['bytes']
        scripts = []
        for item in members:
            name = item['path']
            if item['bytes'] < 150000 and (name.endswith(('.sh', '.rc', '.xml', '.prop')) or
                                         name.endswith(('update-binary', 'updater-script'))):
                destination = ROOT / 'evidence/upstream-text' / name
                # Zip member names are untrusted external data.
                if not destination.resolve().is_relative_to((ROOT / 'evidence/upstream-text').resolve()):
                    raise ValueError('Unsafe archive name')
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(archive.read(name))
                scripts.append(name)
    report = dict(inspected_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  release_url=release['html_url'], package_sha256=SHA, package_bytes=SIZE,
                  uncompressed_member_bytes=sum(i['bytes'] for i in members),
                  bytes_by_top_directory=groups, members=members,
                  extracted_text_only=scripts, executed=False, installed=False,
                  full_image_fit_verified=False, device_runtime_verified=False)
    (ROOT / 'evidence/package-inventory.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('members', 'extracted_text_only')}, indent=2))


if __name__ == '__main__':
    main()
