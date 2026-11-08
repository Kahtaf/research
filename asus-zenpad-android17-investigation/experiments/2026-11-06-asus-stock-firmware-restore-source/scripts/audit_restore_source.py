#!/usr/bin/env python3
"""Audit an immutable OEM payload using bounded memory; never write an image."""
from pathlib import Path
import hashlib
import json
import struct
import zipfile

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
ZIP = WORKSPACE / '2026-11-05-asus-latest-android-feasibility/downloads/UL-P00A_2-WW-5.3.20.0-user.zip'
ZIP_HASH = 'eea443c205596106f041f1054fcbed0158c6c7986b899b9545d84fcd9d38a81c'
BLOCK = 4096
SYSTEM_BLOCKS = 916480
PARTITION_BYTES = 16740352
CHUNK = 1024 * 1024
FINGERPRINT = 'asus/WW_P00A/P00A_2:7.0/NRD90M/WW_P00A-V5.3.20-20180809:user/release-keys'

def require(condition, message):
    if not condition:
        raise ValueError(message)

def file_hash(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        while chunk := stream.read(CHUNK):
            h.update(chunk)
    return h.hexdigest()

def parse_transfer(data, total_blocks):
    lines = data.decode('ascii').splitlines()
    require(len(lines) >= 5 and lines[0] == '4', 'Expected transfer-list version 4')
    require(lines[2:4] == ['0', '0'], 'Stash-dependent updates are unsupported')
    declared = int(lines[1])
    segments = []
    new_offset = 0
    for line in lines[4:]:
        words = line.split()
        require(len(words) == 2 and words[0] in ('new', 'zero', 'erase'), 'Unsupported transfer command')
        kind, ranges = words
        numbers = [int(x) for x in ranges.split(',')]
        require(numbers[0] == len(numbers) - 1 and numbers[0] > 0 and numbers[0] % 2 == 0,
                'Malformed range count')
        for start, end in zip(numbers[1::2], numbers[2::2]):
            require(0 <= start < end <= total_blocks, 'Range exceeds measured partition')
            segments.append((start, end, kind, new_offset if kind == 'new' else None))
            if kind == 'new':
                new_offset += (end - start) * BLOCK
    segments.sort()
    end = 0
    stream_offset = 0
    defined_blocks = 0
    for start, stop, kind, offset in segments:
        require(start == end, 'Overlapping ranges or incomplete partition coverage')
        if kind != 'erase':
            defined_blocks += stop - start
        if kind == 'new':
            require(offset == stream_offset, 'New ranges require non-sequential payload reads')
            stream_offset += (stop - start) * BLOCK
        end = stop
    require(end == total_blocks, 'Transfer list leaves a partition tail unspecified')
    require(defined_blocks == declared, 'Transfer-list defined-block count differs')
    return segments, new_offset

def payload_hashes(segments, stream):
    canonical = hashlib.sha256()
    defined = hashlib.sha256()
    data_hash = hashlib.sha256()
    zeros = bytes(CHUNK)
    consumed = 0
    for start, stop, kind, offset in segments:
        if kind != 'erase':
            defined.update(struct.pack('<QQ', start, stop))
        remaining = (stop - start) * BLOCK
        while remaining:
            amount = min(CHUNK, remaining)
            if kind == 'new':
                chunk = stream.read(amount)
                require(len(chunk) == amount, 'Truncated new-data payload')
                consumed += amount
                data_hash.update(chunk)
            else:
                chunk = zeros[:amount]
            canonical.update(chunk)
            if kind != 'erase':
                defined.update(chunk)
            remaining -= amount
    require(stream.read(1) == b'', 'Unexpected bytes after the new-data payload')
    return {'canonical_zero_discard_sha256': canonical.hexdigest(),
            'defined_ranges_sha256': defined.hexdigest(),
            'defined_ranges_digest_encoding': 'ordered little-endian uint64 start,end; then range bytes; erase omitted',
            'new_dat_sha256': data_hash.hexdigest(), 'new_dat_bytes_read': consumed}

def main():
    output = ROOT / 'evidence'
    output.mkdir(exist_ok=True)
    require(file_hash(ZIP) == ZIP_HASH, 'ASUS ZIP hash differs from the pinned download')
    with zipfile.ZipFile(ZIP) as archive:
        metadata = dict(line.split('=', 1) for line in archive.read('META-INF/com/android/metadata').decode().splitlines())
        require(metadata.get('post-build') == FINGERPRINT, 'OEM target fingerprint mismatch')
        transfer = archive.read('system.transfer.list')
        segments, new_size = parse_transfer(transfer, SYSTEM_BLOCKS)
        require(archive.getinfo('system.new.dat').file_size == new_size, 'Declared new-data size mismatch')
        require(archive.getinfo('system.patch.dat').file_size == 0, 'Incremental patch payload is unsupported')
        with archive.open('system.new.dat') as stream:
            hashes = payload_hashes(segments, stream)
        boot = archive.read('boot.img')
        require(0 < len(boot) <= PARTITION_BYTES, 'OEM boot member exceeds physical partition')
        padded = boot + bytes(PARTITION_BYTES - len(boot))
        backups = WORKSPACE / '2026-11-05-asus-boot-access-audit/artifacts/device-backup'
        comparisons = {label: (backups / label / 'boot.bin').read_bytes() == padded
                       for label in ('initial', 'verify')}
    mapping = (json.dumps({'block_bytes': BLOCK, 'total_blocks': SYSTEM_BLOCKS,
                           'segments': segments}, separators=(',', ':')) + '\n').encode()
    (output / 'system-block-map.json').write_bytes(mapping)
    counts = {kind: sum(stop - start for start, stop, k, _ in segments if k == kind)
              for kind in ('new', 'zero', 'erase')}
    result = {'scope': 'Offline OEM payload audit; no device operation or image output',
              'zip': str(ZIP), 'zip_sha256': ZIP_HASH, 'target_fingerprint': FINGERPRINT,
              'system_bytes': SYSTEM_BLOCKS * BLOCK, 'system_block_counts': counts,
              'complete_nonoverlapping_coverage': True,
              'transfer_list_sha256': hashlib.sha256(transfer).hexdigest(),
              'block_map_sha256': hashlib.sha256(mapping).hexdigest(), **hashes,
              'boot_member_bytes': len(boot), 'boot_member_sha256': hashlib.sha256(boot).hexdigest(),
              'zero_padded_boot_sha256': hashlib.sha256(padded).hexdigest(),
              'padded_boot_matches_original_backups': comparisons,
              'actual_system_backup_comparison': 'pending',
              'discard_ranges_zero_on_actual_tablet': 'unproved',
              'ready_to_flash': False}
    (output / 'audit.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
