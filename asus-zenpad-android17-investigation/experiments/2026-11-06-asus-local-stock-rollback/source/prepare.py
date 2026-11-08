#!/usr/bin/env python3
"""Build only local rollback files. PLAN_ONLY unless --execute. No network/device APIs."""
import argparse
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
PARSER = WORKSPACE / '2026-11-06-asus-stock-firmware-restore-source/scripts/audit_restore_source.py'
PARSER_SHA = '0df55354cd7360f691098672637def9b7274e90c3bab3eadd20b160a34c36365'
MANIFEST = WORKSPACE / '2026-11-06-asus-stock-system-backup-continuation/evidence/runs/20261106T172146Z-89fc7700813aad85/manifest.json'
MANIFEST_SHA = '7d6052ca349d56e6cc83eb276988596c99d1c455926a0018aeaf2d3472947673'
BACKUPS = WORKSPACE / '2026-11-05-asus-boot-access-audit/artifacts/device-backup'
SYSTEM_SHA = '4597a7b5a9f30f9e851f1ae71b54a2db1845465e36a1a55b70ae26e171d5cd49'
BOOT_SHA = '7bb68511b1ade34d24c3e932da7260e6753fa87270bd8249a7218755a5df3316'
RECOVERY_SHA = '902b2f06a01cca574b4aa374e67c4e7f8f0ed53f6e6a55017b6d96351f0f1f20'
BLOCK = 4096
BUFFER = 1024 * 1024
SYSTEM_BYTES = 3753902080
PARTITION_BYTES = 16740352
RESERVE_BYTES = 5 * 1024**3


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def file_hash(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        while data := stream.read(BUFFER):
            result.update(data)
    return result.hexdigest()


def read_exact(stream, count):
    parts = []
    while count:
        value = stream.read(count)
        require(0 < len(value) <= count, 'Truncated or oversized input read')
        parts.append(value)
        count -= len(value)
    return b''.join(parts)


def validate_segments(segments, total_bytes):
    require(type(total_bytes) is int and total_bytes > 0 and total_bytes % BLOCK == 0,
            'Invalid partition extent')
    position = new_offset = 0
    for start, end, kind, offset in segments:
        require(type(start) is int and type(end) is int and 0 <= start < end and
                start * BLOCK == position and end * BLOCK <= total_bytes,
                'Noncontiguous, overlapping or oversized segment')
        require(kind in ('new', 'zero', 'erase'), 'Unsupported reconstruction operation')
        require(offset == new_offset if kind == 'new' else offset is None,
                'Nonsequential payload or invalid non-data offset')
        if kind == 'new':
            new_offset += (end - start) * BLOCK
        position = end * BLOCK
    require(position == total_bytes, 'Incomplete partition coverage')
    return new_offset


def reconstruct(segments, stream, output, total_bytes):
    """Sequentially materialize every byte, including zero and erased ranges."""
    validate_segments(segments, total_bytes)
    zeros = bytes(BUFFER)
    result = hashlib.sha256()
    for start, end, kind, _ in segments:
        remaining = (end - start) * BLOCK
        while remaining:
            amount = min(BUFFER, remaining)
            data = read_exact(stream, amount) if kind == 'new' else zeros[:amount]
            require(output.write(data) == amount, 'Short output write')
            result.update(data)
            remaining -= amount
    require(stream.read(1) == b'', 'Trailing OEM payload')
    return result.hexdigest()


def verify_chunks(path, rows, total_bytes, expected_sha):
    require(path.is_file() and not path.is_symlink() and path.stat().st_size == total_bytes,
            'Output missing or wrong size')
    position = 0
    whole = hashlib.sha256()
    with path.open('rb') as stream:
        for index, row in enumerate(rows):
            require(row['index'] == index and row['offset'] == position and
                    type(row['bytes']) is int and 0 < row['bytes'] <= 32 * BUFFER,
                    'Invalid backup chunk geometry')
            expected = row['remote_sha256']
            require(expected == row['sha256_a'] == row['sha256_b'], 'Backup capture disagreement')
            remaining = row['bytes']
            chunk_hash = hashlib.sha256()
            while remaining:
                data = read_exact(stream, min(BUFFER, remaining))
                whole.update(data)
                chunk_hash.update(data)
                remaining -= len(data)
            require(chunk_hash.hexdigest() == expected, 'Output differs from actual captured chunk ' + str(index))
            position += row['bytes']
        require(position == total_bytes and stream.read(1) == b'', 'Incomplete/trailing output')
    require(whole.hexdigest() == expected_sha, 'Whole output differs from actual stock image')
    return {'bytes': position, 'sha256': whole.hexdigest(), 'verified_chunks': len(rows)}


def load_inputs():
    require(file_hash(PARSER) == PARSER_SHA, 'Pinned transfer-list parser changed')
    spec = importlib.util.spec_from_file_location('pinned_oem_parser', PARSER)
    parser = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(parser)
    require(file_hash(MANIFEST) == MANIFEST_SHA, 'Actual-backup manifest changed')
    backup = json.loads(MANIFEST.read_text())
    require(backup['schema'] == 2 and backup['bytes'] == SYSTEM_BYTES and
            backup['assembled_sha256'] == SYSTEM_SHA and len(backup['chunks']) == 112,
            'Actual backup identity/extent mismatch')
    require(backup['target']['serial'] == 'DEVICE_SERIAL_REDACTED' and
            backup['target']['block'] == '/dev/block/mmcblk0p25' and
            backup['target']['fingerprint'] == parser.FINGERPRINT, 'Wrong physical backup target')
    originals = {}
    for name, expected in [('boot', BOOT_SHA), ('recovery', RECOVERY_SHA)]:
        values = [(BACKUPS / label / (name + '.bin')).read_bytes() for label in ('initial', 'verify')]
        require(values[0] == values[1] and len(values[0]) == PARTITION_BYTES and
                digest(values[0]) == expected, 'Both original ' + name + ' backups required')
        originals[name] = values[0]
    return parser, backup, originals


def prepare():
    parser, backup, originals = load_inputs()
    artifacts = ROOT / 'artifacts'
    artifacts.mkdir(exist_ok=True)
    pending, final = artifacts / 'stock-rollback.pending', artifacts / 'stock-rollback'
    require(not pending.exists() and not pending.is_symlink() and
            not final.exists() and not final.is_symlink(), 'Existing output; inspect it instead of overwriting')
    require(shutil.disk_usage(ROOT).free >= SYSTEM_BYTES + PARTITION_BYTES * 2 + RESERVE_BYTES,
            'Insufficient free disk while retaining 5 GiB reserve')
    require(file_hash(parser.ZIP) == parser.ZIP_HASH, 'Pinned ASUS ZIP changed')
    pending.mkdir(mode=0o700)
    with zipfile.ZipFile(parser.ZIP) as archive:
        metadata = dict(line.split('=', 1) for line in archive.read('META-INF/com/android/metadata').decode().splitlines())
        require(metadata.get('post-build') == parser.FINGERPRINT, 'OEM fingerprint mismatch')
        transfer = archive.read('system.transfer.list')
        segments, new_size = parser.parse_transfer(transfer, parser.SYSTEM_BLOCKS)
        require(archive.getinfo('system.new.dat').file_size == new_size and
                archive.getinfo('system.patch.dat').file_size == 0, 'Unsupported OEM payload sizes')
        with archive.open('system.new.dat') as stream, (pending / 'system.img').open('xb') as output:
            system_sha = reconstruct(segments, stream, output, SYSTEM_BYTES)
            output.flush()
            os.fsync(output.fileno())
        require(system_sha == SYSTEM_SHA, 'Reconstructed SYSTEM differs from captured stock')
        boot = archive.read('boot.img')
        require(0 < len(boot) <= PARTITION_BYTES and
                boot + bytes(PARTITION_BYTES - len(boot)) == originals['boot'], 'OEM BOOT differs from captured original')
    records = {'system.img': verify_chunks(pending / 'system.img', backup['chunks'], SYSTEM_BYTES, SYSTEM_SHA)}
    for name, data in originals.items():
        path = pending / (name + '.img')
        with path.open('xb') as output:
            require(output.write(data) == len(data), 'Short ' + name + ' write')
            output.flush()
            os.fsync(output.fileno())
        require(file_hash(path) == digest(data), 'Independent ' + name + ' readback mismatch')
        records[path.name] = {'bytes': len(data), 'sha256': digest(data), 'verified_original_copies': 2}
    result = {'schema': 1, 'recorded_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'status': 'LOCAL_SELECTED_STOCK_BYTES_VERIFIED', 'files': records,
              'fingerprint': parser.FINGERPRINT, 'hardware_serial': backup['target']['serial'],
              'oem_zip_sha256': parser.ZIP_HASH, 'actual_backup_manifest_sha256': MANIFEST_SHA,
              'transfer_list_sha256': digest(transfer), 'parser_sha256': PARSER_SHA,
              'builder_sha256': file_hash(Path(__file__)), 'network_operations': 0,
              'device_operations': 0, 'full_updater_extracted_or_executed': False,
              'data_or_factory_calibration_included': False, 'ready_to_flash': False,
              'system_source': 'OEM canonical reconstruction, independently equal to all actual-backup chunks and whole hash'}
    (pending / 'actual-stock-system-manifest.json').write_bytes(MANIFEST.read_bytes())
    (pending / 'READY.json').write_text(json.dumps(result, indent=2) + '\n')
    for path in pending.iterdir():
        path.chmod(0o400)
    pending.rename(final)
    print(json.dumps({'output': str(final), **result}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    if args.execute:
        prepare()
    else:
        print(json.dumps({'mode': 'PLAN_ONLY', 'output': str(ROOT / 'artifacts/stock-rollback'),
                          'system_bytes': SYSTEM_BYTES, 'network_operations': 0, 'device_operations': 0,
                          'ready_to_flash': False}, indent=2))


if __name__ == '__main__':
    main()
