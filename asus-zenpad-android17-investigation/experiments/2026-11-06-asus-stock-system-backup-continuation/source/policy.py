"""Fixed stock-system-only scope; shared by local coordinator and remote worker."""
import hashlib
import json
import os
from pathlib import Path
import re
import stat

SERIAL = 'DEVICE_SERIAL_REDACTED'
ENDPOINT = 'IP_REDACTED:5555'
TRANSPORT = dict(kind='adb-tcp', endpoint=ENDPOINT, secure_adb='1')
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

SOURCE_NAMES = {'policy.py', 'remote_worker.py', 'stock_system_backup.py', 'health.py', 'continuation.py'}
CONSTRUCTION = 'ordered-double-capture-chunks; actual-assembly-sha256; independent-full-readback'

def valid_hash(value):
    require(isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value), 'Invalid SHA256')
    return value

def validate_rows(rows, full=False):
    require(isinstance(rows, list) and (len(rows) == len(chunk_layout()) if full else 0 < len(rows) <= len(chunk_layout())),
            'Missing/excess prefix chunks')
    for row, (i, offset, length) in zip(rows, chunk_layout()):
        require(all(type(row.get(key)) is int for key in ('index', 'offset', 'bytes')), 'Invalid chunk number types')
        require((row.get('index'), row.get('offset'), row.get('bytes')) == (i, offset, length), 'Chunk gap/overlap/geometry mismatch')
        require(valid_hash(row.get('sha256_a')) == row.get('sha256_b') == row.get('remote_sha256'), 'Chunk hashes disagree')
        origin = row['source_capture']
        valid_run(origin['run'])
        require(origin['transport'] in (TRANSPORT, dict(kind='adb-usb', serial=SERIAL)), 'Invalid capture transport')
        names = set(origin['source_code_sha256'])
        require(names in (SOURCE_NAMES, {'policy.py', 'remote_worker.py', 'stock_system_backup.py'}), 'Capture source pins missing')
        for value in origin['source_code_sha256'].values():
            valid_hash(value)
        for name in ('helper_sha256', 'root_binary_sha256', 'receipt_sha256'):
            valid_hash(origin[name])

def validate_manifest(m, run):
    require(m.get('schema') == 2 and m.get('run') == valid_run(run) and m.get('target') == TARGET,
            'Wrong manifest identity/scope')
    require(m.get('transport') == TRANSPORT, 'Wrong manifest transport/security')
    require(m.get('construction') == CONSTRUCTION and m.get('bytes') == SIZE, 'Wrong aggregate construction')
    require(not any(k in m for k in ('source_sha256_a', 'source_sha256_b', 'source_bytes_a', 'source_bytes_b')),
            'Cannot claim a contiguous whole-source pass for continued captures')
    valid_hash(m.get('assembled_sha256'))
    valid_hash(m.get('reviewed_input_sha256'))
    validate_rows(m.get('chunks'), full=True)
    require(set(m.get('source_code_sha256', {})) == SOURCE_NAMES, 'Source code provenance missing')
    for value in m['source_code_sha256'].values():
        valid_hash(value)
    valid_hash(m.get('helper_sha256'))
    valid_hash(m.get('root_binary_sha256'))
