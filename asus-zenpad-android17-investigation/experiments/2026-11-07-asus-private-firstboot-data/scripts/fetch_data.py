"""Download one immutable public DATA image into a private sparse working file."""
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SIZE = 11331268096
EXPECTED = '1602ea3644246871468b6987bc90e9a6e0c430f6b46efb4e79cc3555b688e0c1'
SOURCE = '/srv/android/asus-internal-data-validation/artifacts/A17DATA-pristine.raw'


def main():
    os.umask(0o077)
    private = ROOT / 'private'
    private.mkdir(mode=0o700, exist_ok=True)
    if private.is_symlink() or private.stat().st_mode & 0o077:
        raise RuntimeError('Private directory permissions')
    if shutil.disk_usage(private).free < SIZE + 2 * 1024**3:
        raise RuntimeError('Insufficient worst-case free space')
    output = private / 'firstboot-data.raw'
    receipt = private / 'pristine-download.json'
    if output.exists() or receipt.exists():
        raise RuntimeError('Preserve existing download; do not overwrite or retry')
    spec = importlib.util.spec_from_file_location(
        'remote', ROOT.parent / '2026-11-06-asus-product-input-build-kit/scripts/remote.py')
    remote = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(remote)
    info = json.loads(remote.run(
        'from pathlib import Path\nimport json,stat\n'
        f'p=Path({SOURCE!r});s=p.stat()\n'
        'print(json.dumps(dict(size=s.st_size,mode=stat.S_IMODE(s.st_mode),'
        'regular=stat.S_ISREG(s.st_mode),symlink=p.is_symlink())))\n'))
    if info != dict(size=SIZE, mode=0o400, regular=True, symlink=False):
        raise RuntimeError('Immutable public source mismatch')
    process = subprocess.Popen(remote.SSH + [f'gzip -1 -c -- {SOURCE}'],
                               stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    total = 0
    digest = hashlib.sha256()
    try:
        with output.open('xb', buffering=0) as target:
            with gzip.GzipFile(fileobj=process.stdout) as stream:
                while True:
                    chunk = stream.read(1024 * 1024)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > SIZE:
                        raise RuntimeError('Source exceeds admitted length')
                    digest.update(chunk)
                    if not any(chunk):
                        target.seek(len(chunk), os.SEEK_CUR)
                    else:
                        pending = memoryview(chunk)
                        while pending:
                            written = target.write(pending)
                            if not written:
                                raise OSError('Short local write')
                            pending = pending[written:]
            target.truncate(total)
            os.fsync(target.fileno())
        error = process.stderr.read(8192)
        status = process.wait(timeout=30)
        if status or error or total != SIZE or digest.hexdigest() != EXPECTED:
            raise RuntimeError('Download hash/size/transport mismatch')
        with receipt.open('x') as stream:
            json.dump(dict(source=SOURCE, size=total, sha256=digest.hexdigest(),
                           source_preserved=True, local_sparse_bytes=output.stat().st_blocks * 512,
                           private_payload_uploaded=False), stream, indent=2)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        print(json.dumps(dict(download_verified=True, bytes=total,
                              allocated_bytes=output.stat().st_blocks * 512)))
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        process.stdout.close()
        process.stderr.close()


if __name__ == '__main__':
    main()
