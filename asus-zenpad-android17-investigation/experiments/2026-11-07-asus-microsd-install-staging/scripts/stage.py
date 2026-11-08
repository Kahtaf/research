"""Stage actual fixed DATA and original OS chunks; no device/card operations."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT.parent
CHUNK = 1048576
STOCK = BASE / '2026-11-06-asus-local-stock-rollback/artifacts/stock-rollback'
DATA = BASE / '2026-11-07-asus-private-firstboot-data/private/firstboot-data.raw'
SOURCES = [
    (0, STOCK / 'system.img', 3753902080, '4597a7b5a9f30f9e851f1ae71b54a2db1845465e36a1a55b70ae26e171d5cd49', 'stock'),
    (1, STOCK / 'boot.img', 16740352, '7bb68511b1ade34d24c3e932da7260e6753fa87270bd8249a7218755a5df3316', 'stock'),
    (4, DATA, 11331268096, 'cf433efa509f09814bff0877368f0c1b811b7615eefd3cd2a02f58b57995131b', 'install'),
]


def write_new(path, data):
    with path.open('xb') as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())


def stage(role, source, size, expected, group, private):
    if source.is_symlink() or not stat.S_ISREG(source.stat().st_mode) or source.stat().st_size != size:
        raise RuntimeError('Fixed image source mismatch')
    before = source.stat()
    out = private / group / ('role-' + str(role))
    out.mkdir(parents=True, mode=0o700)
    full = hashlib.sha256()
    chunks = []
    payload_bytes = 0
    with source.open('rb') as f:
        for index, offset in enumerate(range(0, size, CHUNK)):
            n = min(CHUNK, size - offset)
            data = f.read(n)
            if len(data) != n:
                raise RuntimeError('Source short read')
            full.update(data)
            sha = hashlib.sha256(data).hexdigest()
            zero = data.count(0) == n
            if not zero:
                p = out / f'{index:06d}.raw'
                write_new(p, data)
                if p.stat().st_size != n or hashlib.sha256(p.read_bytes()).hexdigest() != sha:
                    raise RuntimeError('Staged chunk readback failed')
                p.chmod(0o400)
                payload_bytes += n
            chunks.append(dict(index=index, bytes=n, sha256=sha, omitted_zero=zero))
        if f.read(1):
            raise RuntimeError('Source grew')
    after = source.stat()
    if full.hexdigest() != expected or (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns):
        raise RuntimeError('Complete source identity failed')
    fd = os.open(out, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)
    return dict(role=role, bytes=size, sha256=expected, chunks=chunks,
                payload_bytes=payload_bytes, present_chunks=sum(not r['omitted_zero'] for r in chunks))


def main():
    os.umask(0o077)
    private = ROOT / 'private'
    private.mkdir(mode=0o700)
    if shutil.disk_usage(private).free < sum(row[2] for row in SOURCES) + 1024**3:
        raise RuntimeError('Insufficient worst-case staging space')
    rows = []
    for role, source, size, expected, group in SOURCES:
        rows.append(stage(role, source, size, expected, group, private))
    result = dict(status='PARTIAL_REAL_SOURCES_NO_EXECUTION_TRIGGER', chunk_bytes=CHUNK,
                  roles=rows, missing_install_roles=[2, 3], source_payload_uploaded=False,
                  device_operations=False, card_operations=False, armed=False)
    write_new(private / 'staging.json', (json.dumps(result, indent=2)+'\n').encode())
    public = {k:v for k,v in result.items() if k != 'roles'}
    public['roles'] = [{k:v for k,v in r.items() if k != 'chunks'} for r in rows]
    (ROOT / 'evidence').mkdir()
    write_new(ROOT / 'evidence/staged.json', (json.dumps(public, indent=2)+'\n').encode())
    print(json.dumps(public))


if __name__ == '__main__':
    main()
