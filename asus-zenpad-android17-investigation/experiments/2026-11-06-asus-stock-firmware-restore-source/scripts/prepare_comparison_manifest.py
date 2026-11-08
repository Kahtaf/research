#!/usr/bin/env python3
"""Bounded OEM comparison digests; never contacts a target or writes an image."""
from pathlib import Path
import hashlib
import json
import struct
import zipfile
from audit_restore_source import (ROOT, ZIP, ZIP_HASH, BLOCK, SYSTEM_BLOCKS,
                                  FINGERPRINT, require, file_hash, parse_transfer)
BUFFER = 1024 * 1024
BACKUP_CHUNK = 32 * 1024 * 1024
CANONICAL_SHA = '4597a7b5a9f30f9e851f1ae71b54a2db1845465e36a1a55b70ae26e171d5cd49'
DEFINED_SHA = '9cbdeef3db97aeae5b68a9e01e7869b6c735c108a9f6ab51c803730a847f11df'
NEW_DAT_SHA = 'bf0dd2113b28bc44305c8539201da09432a0932382c656b4a82005211f786aa2'


def comparison_digests(segments, stream, total_bytes, chunk_bytes=BACKUP_CHUNK):
    require(total_bytes > 0 and chunk_bytes > 0 and chunk_bytes % BLOCK == 0,
            'Invalid comparison geometry')
    expected_start = 0
    expected_new_offset = 0
    # This API also checks its boundary; do not assume a caller parsed the list.
    for start, end, kind, offset in segments:
        require(type(start) is int and type(end) is int and
                0 <= start < end and start * BLOCK == expected_start and
                end * BLOCK <= total_bytes, 'Noncontiguous/oversized comparison map')
        require(kind in ('new', 'zero', 'erase'), 'Unknown comparison command')
        if kind == 'new':
            require(offset == expected_new_offset, 'Nonsequential new payload')
            expected_new_offset += (end - start) * BLOCK
        else:
            require(offset is None, 'Non-data command has an input offset')
        expected_start = end * BLOCK
    require(expected_start == total_bytes, 'Incomplete comparison coverage')
    zeros = bytes(BUFFER)
    full = hashlib.sha256()
    full_defined = hashlib.sha256()
    new_data = hashlib.sha256()
    canonical = hashlib.sha256()
    defined = hashlib.sha256()
    defined_bytes = 0
    chunk_start = 0
    chunk_end = min(chunk_bytes, total_bytes)
    rows = []
    for start, end, kind, offset in segments:
        pos, stop = start * BLOCK, end * BLOCK
        if kind != 'erase':
            full_defined.update(struct.pack('<QQ', start, end))
        while pos < stop:
            if kind != 'erase' and (pos == start * BLOCK or pos == chunk_start):
                defined.update(struct.pack('<QQ', pos, min(stop, chunk_end)))
            amount = min(BUFFER, stop - pos, chunk_end - pos)
            data = stream.read(amount) if kind == 'new' else zeros[:amount]
            require(len(data) == amount, 'Truncated OEM new-data payload')
            full.update(data)
            canonical.update(data)
            if kind == 'new':
                new_data.update(data)
            if kind != 'erase':
                full_defined.update(data)
                defined.update(data)
                defined_bytes += amount
            pos += amount
            if pos == chunk_end:
                rows.append(dict(index=len(rows), offset=chunk_start,
                                 bytes=chunk_end - chunk_start,
                                 canonical_zero_erase_sha256=canonical.hexdigest(),
                                 defined_bytes=defined_bytes,
                                 defined_slices_sha256=defined.hexdigest()))
                chunk_start = chunk_end
                chunk_end = min(chunk_end + chunk_bytes, total_bytes)
                canonical, defined, defined_bytes = hashlib.sha256(), hashlib.sha256(), 0
    require(stream.read(1) == b'', 'Trailing OEM new-data payload')
    require(sum(row['bytes'] for row in rows) == total_bytes, 'Incomplete chunk coverage')
    return dict(chunks=rows, canonical_zero_erase_sha256=full.hexdigest(),
                defined_ranges_sha256=full_defined.hexdigest(),
                new_dat_sha256=new_data.hexdigest())


def main():
    require(file_hash(ZIP) == ZIP_HASH, 'Pinned ASUS ZIP changed')
    output = ROOT / 'evidence/oem-comparison-chunks.json'
    require(not output.exists() and not output.is_symlink(), 'Comparison output already exists')
    with zipfile.ZipFile(ZIP) as archive:
        metadata = dict(line.split('=', 1) for line in
                        archive.read('META-INF/com/android/metadata').decode().splitlines())
        require(metadata.get('post-build') == FINGERPRINT, 'OEM fingerprint changed')
        transfer = archive.read('system.transfer.list')
        segments, new_size = parse_transfer(transfer, SYSTEM_BLOCKS)
        require(archive.getinfo('system.new.dat').file_size == new_size, 'OEM input length changed')
        require(archive.getinfo('system.patch.dat').file_size == 0, 'Unsupported incremental patch')
        with archive.open('system.new.dat') as stream:
            result = comparison_digests(segments, stream, SYSTEM_BLOCKS * BLOCK)
    require(result['canonical_zero_erase_sha256'] == CANONICAL_SHA and
            result['defined_ranges_sha256'] == DEFINED_SHA and
            result['new_dat_sha256'] == NEW_DAT_SHA, 'Independent prior OEM audit mismatch')
    result.update(schema=1, purpose='OEM comparison only; never a substitute for actual backup verification',
                  zip_sha256=ZIP_HASH, target_fingerprint=FINGERPRINT,
                  block_bytes=BLOCK, system_bytes=SYSTEM_BLOCKS * BLOCK, chunk_bytes=BACKUP_CHUNK,
                  transfer_list_sha256=hashlib.sha256(transfer).hexdigest(),
                  segments=segments,
                  defined_slices_digest_encoding='per chunk, each non-erase segment slice: absolute byte start/end as LE uint64 pair then actual bytes',
                  defined_ranges_digest_encoding='each complete non-erase segment: block start/end as LE uint64 pair then actual bytes',
                  physical_backup_verified=False, ready_to_flash=False)
    with output.open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps(dict(output=str(output), output_sha256=file_hash(output),
                          chunks=len(result['chunks']), bytes=result['system_bytes'],
                          canonical_sha256=CANONICAL_SHA, physical_backup_verified=False), indent=2))


if __name__ == '__main__':
    main()
