"""Executed over authenticated SSH only by explicit coordinator execution.

stdin is bytes exclusively during put; the program/request arrive as quoted argv.
The standalone CLI has no configurable destination or partition.
"""
import json
import os
from pathlib import Path
import shutil
import sys
import hashlib
from policy import (REMOTE_BASE, SIZE, CHUNK, BUFFER, Stop, require, valid_run,
                    private, ancestors, create_file, fsync_dir, encoded, sha,
                    digest_file, chunk_layout, validate_manifest)


def base_check(create=False):
    ancestors(REMOTE_BASE)
    if create and not os.path.lexists(REMOTE_BASE):
        REMOTE_BASE.mkdir(mode=0o700)
    private(REMOTE_BASE, directory=True)


def run_dir(run):
    base_check()
    p = REMOTE_BASE / valid_run(run)
    private(p, directory=True)
    return p


def verify_files(p, m):
    validate_manifest(m, p.name)
    for row in m['chunks']:
        f = p / ('chunk-%04d.bin' % row['index'])
        private(f)
        require(digest_file(f) == (row['bytes'], row['sha256_a']), 'Stored chunk readback mismatch')
    private(p / 'system.img')
    n, h = digest_file(p / 'system.img')
    require((n, h) == (SIZE, m['source_sha256_a']), 'Full assembled readback mismatch')
    return dict(bytes=n, sha256=h)


def dispatch(q, stream):
    os.umask(0o077)
    op, run = q['operation'], valid_run(q['run'])
    if op == 'preflight':
        ancestors(REMOTE_BASE)
        if os.path.lexists(REMOTE_BASE):
            base_check()
        free = shutil.disk_usage(REMOTE_BASE.parent).free
        require(free >= 2 * SIZE + 1024**3, 'Insufficient remote disk for chunks plus assembly plus reserve')
        require(not os.path.lexists(REMOTE_BASE / run), 'Remote run collision')
        return dict(operation=op, run=run, free_bytes=free, required_bytes=2*SIZE+1024**3)
    if op == 'begin':
        dispatch(dict(operation='preflight', run=run), stream)
        base_check(create=True)
        p = REMOTE_BASE / run
        p.mkdir(mode=0o700)  # Collision fails; no resume or overwrite.
        create_file(p / 'RUN.json', encoded(dict(run=run, scope='fixed-stock-system-only')))
        fsync_dir(p)
        fsync_dir(REMOTE_BASE)
        return dict(operation=op, run=run)
    p = run_dir(run)
    private(p / 'RUN.json')
    require(json.loads((p / 'RUN.json').read_bytes()) == dict(run=run, scope='fixed-stock-system-only'), 'Run owner marker mismatch')
    if op == 'put':
        require(not os.path.lexists(p / 'READY.json'), 'Run already published')
        i = q['index']
        require(type(i) is int and 0 <= i < len(chunk_layout()), 'Invalid chunk index')
        _, _, length = chunk_layout()[i]
        require(q['bytes'] == length, 'Chunk size outside fixed geometry')
        f = p / ('chunk-%04d.bin' % i)
        fd = os.open(f, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        h, n = hashlib.sha256(), 0
        with os.fdopen(fd, 'wb') as out:
            while b := stream.read(min(BUFFER, length + 1 - n)):
                n += len(b)
                require(n <= length, 'Oversized upload')
                out.write(b)
                h.update(b)
            out.flush()
            os.fsync(out.fileno())
        require(n == length and h.hexdigest() == q['sha256'], 'Upload short or hash mismatch')
        private(f)
        require(digest_file(f) == (length, q['sha256']), 'Remote actual-byte readback failed')
        fsync_dir(p)
        return dict(operation=op, run=run, index=i, bytes=n, sha256=h.hexdigest())
    if op == 'finalize':
        require(not os.path.lexists(p / 'READY.json'), 'Already published')
        m = q['manifest']
        validate_manifest(m, run)
        raw = encoded(m)
        require(sha(raw) == q['manifest_sha256'], 'Manifest transport mismatch')
        # Preverify every chunk before creating any full image.
        for row in m['chunks']:
            f = p / ('chunk-%04d.bin' % row['index'])
            private(f)
            require(digest_file(f) == (row['bytes'], row['sha256_a']), 'Chunk changed before assembly')
        fd = os.open(p / 'system.img', os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        h, n = hashlib.sha256(), 0
        with os.fdopen(fd, 'wb') as out:
            for row in m['chunks']:
                with (p / ('chunk-%04d.bin' % row['index'])).open('rb') as inp:
                    while b := inp.read(BUFFER):
                        n += len(b)
                        require(n <= SIZE, 'Assembly grew beyond fixed size')
                        out.write(b)
                        h.update(b)
            out.flush()
            os.fsync(out.fileno())
        require((n, h.hexdigest()) == (SIZE, m['source_sha256_a']), 'Assembly hash mismatch')
        result = verify_files(p, m)  # Independent full-file readback, not the write hash.
        create_file(p / 'manifest.json', raw)
        require(digest_file(p / 'manifest.json') == (len(raw), sha(raw)), 'Manifest readback failed')
        ready = dict(run=run, manifest_sha256=sha(raw), **result)
        create_file(p / 'READY.pending', encoded(ready))
        fsync_dir(p)
        # Atomic publication, hard-link O_EXCL semantics; never overwrite READY.
        os.link(p / 'READY.pending', p / 'READY.json', follow_symlinks=False)
        (p / 'READY.pending').unlink()
        fsync_dir(p)
        return dict(operation=op, **ready)
    if op == 'verify':
        private(p / 'READY.json')
        private(p / 'manifest.json')
        raw = (p / 'manifest.json').read_bytes()
        require(len(raw) < 1024*1024 and sha(raw) == q['manifest_sha256'], 'Pinned manifest mismatch')
        m = json.loads(raw)
        result = verify_files(p, m)
        ready = dict(run=run, manifest_sha256=sha(raw), **result)
        require(json.loads((p / 'READY.json').read_bytes()) == ready, 'READY mismatch')
        return dict(operation=op, **ready)
    raise Stop('Unsupported remote operation')


if __name__ == '__main__':
    try:
        print(json.dumps(dispatch(json.loads(sys.argv[1]), sys.stdin.buffer), sort_keys=True))
    except Exception as exc:
        print(type(exc).__name__ + ': ' + str(exc), file=sys.stderr)
        raise SystemExit(2)
