"""Fixed stock-system-only scope; shared by local coordinator and remote worker."""
import hashlib
import json
import os
from pathlib import Path
import re
import stat

SERIAL = 'DEVICE_SERIAL_REDACTED'
FINGERPRINT = 'asus/WW_P00A/P00A_2:7.0/NRD90M/WW_P00A-V5.3.20-20180809:user/release-keys'
BLOCK = '/dev/block/mmcblk0p25'
ALIAS = '/dev/block/platform/mtk-msdc.0/11230000.MSDC0/by-name/system'
SIZE = 3753902080
CHUNK = 32 * 1024 * 1024
BUFFER = 1024 * 1024
REMOTE_BASE = Path('/srv/android/asus-stock-system-backup')
TARGET = dict(serial=SERIAL, product='P00A_2', sdk='24', fingerprint=FINGERPRINT,
              block=BLOCK, by_name=ALIAS, bytes=SIZE, sectors=7331840,
              start_sector=1072424, logical_sector_bytes=512, major_minor='179:25', partition=25)

class Stop(Exception):
    """Stop and retain evidence/staging. Never retry automatically."""

def require(ok, message):
    if not ok:
        raise Stop(message)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2) + '\n').encode()

def valid_run(run):
    require(isinstance(run, str) and re.fullmatch(r'[0-9]{8}T[0-9]{6}Z-[0-9a-f]{16}', run), 'Invalid run id')
    return run

def digest_file(path):
    h, n = hashlib.sha256(), 0
    with Path(path).open('rb') as f:
        while b := f.read(BUFFER):
            h.update(b)
            n += len(b)
    return n, h.hexdigest()

def private(path, directory=False):
    st = Path(path).lstat()
    require((stat.S_ISDIR(st.st_mode) if directory else stat.S_ISREG(st.st_mode))
            and st.st_uid == os.getuid() and stat.S_IMODE(st.st_mode) == (0o700 if directory else 0o600)
            and (directory or st.st_nlink == 1), 'Unsafe owned path: ' + str(path))
    return st

def ancestors(path):
    for p in reversed(Path(path).absolute().parents):
        st = p.lstat()
        require(stat.S_ISDIR(st.st_mode) and st.st_uid in (0, os.getuid())
                and not st.st_mode & 0o022, 'Untrusted parent directory: ' + str(p))

def create_file(path, data):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())

def fsync_dir(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)

def chunk_layout(size=SIZE, chunk=CHUNK):
    return [(i, offset, min(chunk, size-offset)) for i, offset in enumerate(range(0, size, chunk))]

def validate_manifest(m, run):
    require(m.get('schema') == 1 and m.get('run') == valid_run(run) and m.get('target') == TARGET,
            'Wrong manifest identity/scope')
    require(m.get('source_bytes_a') == SIZE == m.get('source_bytes_b'), 'Wrong source aggregate length')
    require(re.fullmatch('[0-9a-f]{64}', m.get('source_sha256_a', '')) is not None
            and m['source_sha256_a'] == m.get('source_sha256_b'), 'Source aggregate mismatch')
    require(len(m.get('chunks', [])) == len(chunk_layout()), 'Missing chunks')
    for row, (i, offset, length) in zip(m['chunks'], chunk_layout()):
        require((row.get('index'), row.get('offset'), row.get('bytes')) == (i, offset, length), 'Chunk geometry mismatch')
        require(re.fullmatch('[0-9a-f]{64}', row.get('sha256_a', '')) is not None
                and row['sha256_a'] == row.get('sha256_b') == row.get('remote_sha256'), 'Chunk hashes disagree')
    require(set(m.get('source_code_sha256', {})) == {'policy.py', 'remote_worker.py', 'stock_system_backup.py'},
            'Source code provenance missing')
    for value in m['source_code_sha256'].values():
        require(re.fullmatch('[0-9a-f]{64}', value) is not None, 'Invalid source code hash')
