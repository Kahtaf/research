#!/usr/bin/env python3
"""Read-only ext4 gate for raw or Android sparse SYSTEM. No payload expansion/hash."""
import argparse
import hashlib
import json
import os
import stat
import struct

PROFILE = (0x28, 0x42, 0x7b)


def need(ok, message):
    if not ok:
        raise ValueError(message)


def read_at(fd, offset, length):
    data = os.pread(fd, length, offset)
    need(len(data) == length, 'Truncated input')
    return data


def superblock(fd, file_bytes):
    """Return logical superblock and size, checking every sparse chunk boundary."""
    header = read_at(fd, 0, 28)
    if struct.unpack_from('<I', header)[0] != 0xed26ff3a:
        return read_at(fd, 1024, 1024), file_bytes, {'format': 'raw'}
    _, major, minor, fh, ch, block, blocks, chunks, checksum = struct.unpack('<I4H4I', header)
    need(major == 1 and 28 <= fh <= 65536 and 12 <= ch <= 65536,
         'Unsupported sparse headers')
    need(block >= 4 and block % 4 == 0 and blocks > 0 and chunks <= 1000000,
         'Invalid sparse geometry')
    position, logical, copied = fh, 0, 0
    sb = bytearray(1024)
    for _ in range(chunks):
        need(position + ch <= file_bytes, 'Sparse header exceeds file')
        kind, reserved, count, total = struct.unpack('<2H2I', read_at(fd, position, 12))
        size = count * block
        expected = {0xcac1: size, 0xcac2: 4, 0xcac3: 0, 0xcac4: 4}.get(kind)
        need(expected is not None and total == ch + expected,
             'Invalid sparse chunk payload')
        need(kind != 0xcac4 or count == 0, 'CRC chunk has blocks')
        need(position + total <= file_bytes and logical + size <= blocks * block,
             'Sparse chunk exceeds declared bounds')
        start, end = max(logical, 1024), min(logical + size, 2048)
        if start < end:
            length = end - start
            if kind == 0xcac1:
                data = read_at(fd, position + ch + start - logical, length)
            elif kind == 0xcac2:
                fill = read_at(fd, position + ch, 4)
                shift = (start - logical) % 4
                data = (fill * ((length + shift + 3) // 4))[shift:shift + length]
            else:
                data = bytes(length)
            sb[start - 1024:end - 1024] = data
            copied += length
        logical += size
        position += total
    need(logical == blocks * block and position == file_bytes and copied == 1024,
         'Sparse length, block total, or superblock coverage mismatch')
    return bytes(sb), logical, {'format': 'android-sparse', 'sparse_block_bytes': block,
                               'sparse_chunks': chunks, 'sparse_crc_verified': False}


def inspect(path, partition_bytes):
    fd = os.open(path, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW)
    try:
        before = os.fstat(fd)
        need(stat.S_ISREG(before.st_mode), 'Require an ordinary completed image file')
        sb, logical, container = superblock(fd, before.st_size)
        u16 = lambda offset: struct.unpack_from('<H', sb, offset)[0]
        u32 = lambda offset: struct.unpack_from('<I', sb, offset)[0]
        need(u16(56) == 0xef53 and u32(76) == 1, 'Require dynamic-revision ext4')
        features = (u32(92), u32(96), u32(100))
        need(features == PROFILE,
             'Unqualified feature profile: ' + '/'.join(hex(x) for x in features))
        need(u32(24) == 2 and u32(28) == 2 and u16(88) == 256,
             'Require 4096-byte blocks/clusters and 256-byte inodes')
        need(u32(20) == 0 and u32(336) == 0 and u16(254) in (0, 32),
             'Unexpected first block, high block count, or descriptor size')
        filesystem_bytes = u32(4) * 4096
        need(0 < filesystem_bytes <= logical <= partition_bytes,
             'Filesystem/container exceeds partition or is truncated')
        need(u16(58) == 1 and u32(232) == 0 and u32(224) == 0 and u32(228) == 0,
             'Require clean filesystem, no orphan head or journal inode/device')
        need(u32(0) > 0 and u32(40) > 0 and u32(32) > 0, 'Invalid inode/group geometry')
        after = os.fstat(fd)
        need((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) ==
             (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns),
             'Input changed during header inspection')
        return dict(header_gate_pass=True, actual_kernel_mount_required=True,
                    path=os.path.realpath(path), file_bytes=after.st_size,
                    expanded_bytes=logical, filesystem_bytes=filesystem_bytes,
                    partition_bytes=partition_bytes, block_bytes=4096, inode_bytes=256,
                    feature_masks=dict(zip(('compat', 'incompat', 'ro_compat'), map(hex, features))),
                    superblock_sha256=hashlib.sha256(sb).hexdigest(),
                    full_image_rehashed=False, **container)
    finally:
        os.close(fd)


def main():
    import resource
    if hasattr(os, 'sched_setaffinity'):
        os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
        resource.setrlimit(resource.RLIMIT_AS, (1024**3, 1024**3))
    resource.setrlimit(resource.RLIMIT_CPU, (60, 60))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('image')
    parser.add_argument('--partition-bytes', type=int, default=3753902080)
    args = parser.parse_args()
    try:
        print(json.dumps(inspect(args.image, args.partition_bytes), indent=2))
    except (ValueError, OSError) as error:
        print(json.dumps({'header_gate_pass': False, 'error': str(error)}))
        raise SystemExit(1)


if __name__ == '__main__':
    main()
