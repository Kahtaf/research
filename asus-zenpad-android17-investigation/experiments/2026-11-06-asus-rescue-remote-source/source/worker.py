"""Read-only raw source worker. CLI admits only embedded fixed profiles.
SRC1 is host-to-source framing; it never reaches the target's unchanged RSC1.
No file creation, subprocesses, retries, target operations or arbitrary paths.
"""
import hashlib
import json
import os
import stat
import struct
import sys

CHUNK = 1048576
MAX_CHUNKS = 10807
HEADER = struct.Struct('<4sII')
REQUEST = struct.Struct('<IQI')
REPLY = struct.Struct('<IQI32s')


def readn(stream, length):
    result = bytearray()
    while len(result) < length:
        block = stream.read(length - len(result))
        if not block:
            raise EOFError('source transport ended; no retry')
        result.extend(block)
    return bytes(result)


def send(stream, op, data=b''):
    block = HEADER.pack(b'SRC1', op, len(data)) + data
    view = memoryview(block)
    while view:
        n = stream.write(view)
        if n is None or n <= 0:
            raise IOError('source short write')
        view = view[n:]
    stream.flush()


def receive(stream, expected=None, limit=CHUNK + REPLY.size):
    magic, op, length = HEADER.unpack(readn(stream, HEADER.size))
    if magic != b'SRC1' or length > limit or (expected is not None and op != expected):
        raise ValueError('invalid source frame/op/length')
    return op, readn(stream, length)


def signature(st):
    return tuple(getattr(st, key) for key in (
        'st_dev', 'st_ino', 'st_mode', 'st_uid', 'st_gid', 'st_nlink',
        'st_size', 'st_mtime_ns', 'st_ctime_ns'))


class HeldRaw:
    def __init__(self, profile):
        self.profile = dict(profile)
        self.path = profile['path']
        self.fd = None
        self.verified = False
        self.dead = False
        self.chunks = None
        self.check_path()
        # NONBLOCK avoids hanging on a substituted FIFO before fstat rejects it.
        self.fd = os.open(self.path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        try:
            st = os.fstat(self.fd)
            if (not stat.S_ISREG(st.st_mode) or st.st_size != profile['size']
                    or stat.S_IMODE(st.st_mode) != profile['mode']
                    or st.st_uid != profile['uid'] or st.st_gid != profile['gid']
                    or st.st_nlink != profile['nlink'] or st.st_nlink != 1
                    or not 0 < st.st_size <= CHUNK * MAX_CHUNKS):
                raise ValueError('source type/size/owner/mode/link guard')
            self.initial = signature(st)
            self.check()
        except BaseException:
            self.close()
            raise

    def check_path(self):
        if not os.path.isabs(self.path) or os.path.normpath(self.path) != self.path:
            raise ValueError('source path must be canonical absolute')
        if os.path.realpath(self.path) != self.path:
            raise ValueError('source symlink/ancestor alias forbidden')

    def check(self):
        if self.dead or self.fd is None:
            raise ValueError('source closed or poisoned')
        try:
            self.check_path()
            if (signature(os.fstat(self.fd)) != self.initial
                    or signature(os.stat(self.path, follow_symlinks=False)) != self.initial):
                raise ValueError('held source/path changed')
        except BaseException:
            self.dead = True
            raise

    def raw_chunk(self, index):
        count = (self.profile['size'] + CHUNK - 1) // CHUNK
        if type(index) is not int or not 0 <= index < count:
            raise ValueError('source chunk index')
        self.check()
        length = min(CHUNK, self.profile['size'] - index * CHUNK)
        data = os.pread(self.fd, length, index * CHUNK)
        self.check()
        if len(data) != length:
            self.dead = True
            raise ValueError('short source read')
        if index == 0 and data[:4] == bytes.fromhex('3aff26ed'):
            self.dead = True
            raise ValueError('Android sparse encoded input forbidden')
        return data

    def preflight(self):
        if self.verified:
            raise ValueError('preflight already consumed')
        full = hashlib.sha256()
        chunks = bytearray()
        try:
            for i in range((self.profile['size'] + CHUNK - 1) // CHUNK):
                data = self.raw_chunk(i)
                full.update(data)
                chunks.extend(hashlib.sha256(data).digest())
            self.check()
            if full.hexdigest() != self.profile['sha256']:
                raise ValueError('whole source SHA mismatch')
            if hashlib.sha256(chunks).hexdigest() != self.profile['chunks_sha256']:
                raise ValueError('source chunk table mismatch')
            self.chunks = bytes(chunks)
            self.verified = True
            return full.digest(), self.chunks
        except BaseException:
            self.dead = True
            raise

    def chunk(self, index):
        if not self.verified:
            raise ValueError('full preflight required')
        data = self.raw_chunk(index)
        if hashlib.sha256(data).digest() != self.chunks[index * 32:(index + 1) * 32]:
            self.dead = True
            raise ValueError('source changed after preflight')
        return data

    def close(self):
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None


def serve(profile, reader, writer):
    source = HeldRaw(profile)
    try:
        send(writer, 0x80, json.dumps({'stat': source.initial, 'profile': profile}).encode())
        sampled = set()
        next_index = 0
        while True:
            op, payload = receive(reader, limit=REQUEST.size)
            if op == 1 and not payload:
                if sampled:
                    raise ValueError('samples cannot become a transfer session')
                full, chunks = source.preflight()
                send(writer, 0x81, full + chunks)
            elif op in (2, 3) and len(payload) == REQUEST.size:
                index, offset, length = REQUEST.unpack(payload)
                size = profile['size']
                count = (size + CHUNK - 1) // CHUNK
                if index >= count or offset != index * CHUNK or length != min(CHUNK, size - offset):
                    raise ValueError('request index/position/length')
                if op == 3:
                    # Explicit bounded sample mode cannot turn into a complete transfer.
                    if source.verified or index not in {0, count // 2, count - 1} or index in sampled:
                        raise ValueError('sample not allowed')
                    sampled.add(index)
                    data = source.raw_chunk(index)
                else:
                    if sampled or index != next_index:
                        raise ValueError('sequential fresh preflight session required')
                    data = source.chunk(index)
                    next_index += 1
                send(writer, 0x80 + op, REPLY.pack(index, offset, length, hashlib.sha256(data).digest()) + data)
            elif op == 4 and not payload:
                source.check()
                send(writer, 0x84)
            elif op == 5 and not payload:
                source.check()
                send(writer, 0x85)
                return
            else:
                raise ValueError('unknown source command')
    finally:
        source.close()


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in FIXED_PROFILES:
        raise ValueError('fixed profile required')
    serve(FIXED_PROFILES[sys.argv[1]], sys.stdin.buffer, sys.stdout.buffer)

# FIXED_PROFILES is embedded below; no environment/user path selection.
FIXED_PROFILES = {'userdata-pristine': {'role': 4, 'path': '/srv/android/asus-internal-data-validation/artifacts/A17DATA-pristine.raw', 'size': 11331268096, 'sha256': '1602ea3644246871468b6987bc90e9a6e0c430f6b46efb4e79cc3555b688e0c1', 'uid': 1001, 'gid': 1002, 'mode': 256, 'nlink': 1, 'chunk_bytes': 1048576, 'count': 10807, 'chunks_sha256': 'eff221a909c654670e2628c19cf6a81d779cb5fadf85dd754b7d4fd38367a5b0'}, 'stock-system': {'role': 0, 'path': '/srv/android/asus-stock-system-backup/20261106T172146Z-89fc7700813aad85/system.img', 'size': 3753902080, 'sha256': '4597a7b5a9f30f9e851f1ae71b54a2db1845465e36a1a55b70ae26e171d5cd49', 'uid': 1001, 'gid': 1002, 'mode': 384, 'nlink': 1, 'chunk_bytes': 1048576, 'count': 3580, 'chunks_sha256': '994b427a2ded325bceb26bda24fea8bf524d5dda432fb1354a11c898b87d2fc8'}}

if __name__ == "__main__":
    main()
