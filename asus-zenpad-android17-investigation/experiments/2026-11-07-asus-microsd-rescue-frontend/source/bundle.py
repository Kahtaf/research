"""Chunk parent-admitted raw files for the fixed SD frontend. PLAN by default.
Workspace layout: admitted.manifest, raw/role-N.raw, card/ (new output).
No device/mount operations; no admissions are created by this utility.
"""
import argparse
import hashlib
import json
import os
import stat
import struct

CHUNK = 1048576
GEOMETRY = {9: 16740352, 25: 3753902080, 26: 11331268096}

def directory(path):
    # Refuse symlinks in every component, including ancestors.
    parts = os.path.abspath(path).split('/')[1:]
    fd = os.open('/', os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in parts:
            other = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = other
        return fd
    except BaseException:
        os.close(fd)
        raise

def ordinary(parent, name, size=None):
    fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
    s = os.fstat(fd)
    if not stat.S_ISREG(s.st_mode) or s.st_nlink != 1 or (size is not None and s.st_size != size):
        os.close(fd)
        raise ValueError('exact ordinary file required: ' + name)
    return fd

def readn(fd, n):
    out = bytearray()
    while len(out) < n:
        b = os.read(fd, n - len(out))
        if not b:
            raise ValueError('short source')
        out.extend(b)
    return bytes(out)

def parse(b, geometry=GEOMETRY):
    if len(b) < 112 or b[:8] != b'ASUSR002' or struct.unpack_from('<I', b, 8)[0] != 2:
        raise ValueError('ASUSR002 required')
    count = struct.unpack_from('<I', b, 12)[0]
    if count not in (2, 4, 5):
        raise ValueError('no admitted roles')
    rows = []
    offset = 112
    for i in range(count):
        if offset + 52 > len(b):
            raise ValueError('truncated record')
        role, part, size, full, n = struct.unpack_from('<IIQ32sI', b, offset)
        offset += 52
        if role != i or part != (26 if i == 4 else 9 if i % 2 else 25) or size != geometry[part] or n != (size + CHUNK - 1) // CHUNK:
            raise ValueError('fixed role geometry required')
        chunks = b[offset:offset+n*32]
        if len(chunks) != n*32:
            raise ValueError('truncated chunk table')
        rows.append(dict(size=size, full=full, chunks=[chunks[j:j+32] for j in range(0, len(chunks), 32)]))
        offset += n*32
    if offset != len(b):
        raise ValueError('trailing bytes')
    return rows

def selection(rows, rollback):
    if rollback is None:
        if len(rows) != 5:
            raise ValueError('normal install requires parent-admitted five-role manifest; stock pair is not Android17 admission')
        return [2, 4, 3]
    return [rollback]

def capacity(rows, roles):
    payload = logical = allocated = files = omitted = 0
    for role in roles:
        row = rows[role]
        logical += row['size']
        for i, digest in enumerate(row['chunks']):
            n = min(CHUNK, row['size'] - i*CHUNK)
            if digest == hashlib.sha256(bytes(n)).digest():
                omitted += 1
            else:
                payload += n
                # FAT cluster size is a later physical-card fact. No fit promise.
                allocated += ((n + 32767) // 32768) * 32768
                files += 1
    return dict(source_payload_bytes=payload, logical_output_bytes=logical,
                present_chunk_files=files, omitted_zero_chunks=omitted,
                chunk_allocation_bytes_if_32KiB_clusters=allocated,
                filesystem_metadata_trigger_and_reports_extra=True,
                includes_rollback_roles=any(role < 2 for role in roles))

def write_file(parent, name, b):
    fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=parent)
    try:
        view = memoryview(b)
        while view:
            n = os.write(fd, view)
            if n <= 0:
                raise OSError('short output')
            view = view[n:]
        os.fsync(fd)
    finally:
        os.close(fd)

def produce(work, b, rows, roles):
    raw = os.open('raw', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=work)
    output = bundle = -1
    try:
        # Exclusive output; failure leaves a visibly incomplete tree. Never resume.
        os.mkdir('card', dir_fd=work)
        output = os.open('card', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=work)
        os.mkdir('asus-rescue', dir_fd=output)
        os.mkdir('asus-rescue-report', dir_fd=output)
        bundle = os.open('asus-rescue', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=output)
        for role in roles:
            row = rows[role]
            fd = ordinary(raw, 'role-%d.raw' % role, row['size'])
            out = -1
            try:
                before = os.fstat(fd)
                os.mkdir('role-%d' % role, dir_fd=bundle)
                out = os.open('role-%d' % role, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=bundle)
                full = hashlib.sha256()
                for i, digest in enumerate(row['chunks']):
                    n = min(CHUNK, row['size'] - i*CHUNK)
                    chunk = readn(fd, n)
                    if i == 0 and chunk[:4] == bytes.fromhex('3aff26ed'):
                        raise ValueError('Android sparse image forbidden')
                    if hashlib.sha256(chunk).digest() != digest:
                        raise ValueError('expected chunk hash mismatch')
                    full.update(chunk)
                    if chunk != bytes(n):
                        write_file(out, '%06d.raw' % i, chunk)
                after = os.fstat(fd)
                identity = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
                if identity(before) != identity(after) or full.digest() != row['full']:
                    raise ValueError('full raw digest/source stability mismatch')
                os.fsync(out)
            finally:
                if out >= 0:
                    os.close(out)
                os.close(fd)
        # Publish binding only after all actual raw/chunk/full hashes passed.
        write_file(bundle, 'manifest.sha256', hashlib.sha256(b).hexdigest().encode() + b'\n')
        os.fsync(bundle)
        os.fsync(output)
        os.fsync(work)
    finally:
        if bundle >= 0:
            os.close(bundle)
        if output >= 0:
            os.close(output)
        os.close(raw)

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('workspace')
    p.add_argument('--rollback-role', type=int, choices=[0, 1])
    p.add_argument('--execute', action='store_true')
    a = p.parse_args()
    work = directory(a.workspace)
    try:
        fd = ordinary(work, 'admitted.manifest')
        try:
            n = os.fstat(fd).st_size
            if not 112 <= n <= CHUNK:
                raise ValueError('manifest length')
            b = readn(fd, n)
        finally:
            os.close(fd)
        rows = parse(b)
        roles = selection(rows, a.rollback_role)
        print(json.dumps(dict(mode='BUILD_BUNDLE' if a.execute else 'PLAN',
                              manifest_sha256=hashlib.sha256(b).hexdigest(), roles=roles,
                              **capacity(rows, roles)), sort_keys=True))
        if a.execute:
            produce(work, b, rows, roles)
    finally:
        os.close(work)

if __name__ == '__main__':
    main()
