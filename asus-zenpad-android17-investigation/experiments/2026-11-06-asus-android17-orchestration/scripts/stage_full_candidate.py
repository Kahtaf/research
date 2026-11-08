#!/usr/bin/env python3
"""Freeze reviewed device source for the full-product integration handoff."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import tarfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT.parent / '2026-11-05-asus-android17-device-product/candidates/full'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('revision')
    args = parser.parse_args()
    if not re.fullmatch(r'r[0-9]+', args.revision):
        parser.error('Use a fresh numbered revision')
    destination = ROOT / 'artifacts' / ('full-product-inputs-' + args.revision + '.tar.gz')
    destination.parent.mkdir(exist_ok=True)
    if destination.exists():
        raise SystemExit('Preserve previous input revision')
    files = sorted((SOURCE / 'device/asus/p00a').rglob('*'))
    if any(p.is_symlink() for p in files):
        raise SystemExit('Review symlink inputs explicitly')
    files = [p for p in files if p.is_file()]
    manifest = dict(scope='Reviewed device inputs including generic firmware; no user keys, calibration, reports or evidence',
                    revision=args.revision, full_build_passed=False,
                    files=[dict(path=str(p.relative_to(SOURCE)), bytes=p.stat().st_size,
                                sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in files])
    data = (json.dumps(manifest, indent=2) + '\n').encode()
    with destination.open('xb') as stream, tarfile.open(fileobj=stream, mode='w:gz') as archive:
        for path in files:
            archive.add(path, arcname=str(path.relative_to(SOURCE)), recursive=False)
        info = tarfile.TarInfo('manifest.json')
        info.size = len(data)
        info.mode = 0o644
        archive.addfile(info, io.BytesIO(data))
    report = dict(archive=destination.name, bytes=destination.stat().st_size,
                  sha256=hashlib.sha256(destination.read_bytes()).hexdigest(), manifest=manifest)
    (ROOT / 'evidence' / ('full-product-inputs-' + args.revision + '.json')).write_text(json.dumps(report, indent=2) + '\n')
    print(f'{destination}: {len(files)} source files, SHA256 {report["sha256"]}')


if __name__ == '__main__':
    main()
