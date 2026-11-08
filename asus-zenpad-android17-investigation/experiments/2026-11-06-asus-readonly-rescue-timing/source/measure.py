"""Measure one fixed original-BOOT reconciliation on an inherited rescue socket.

No discovery, ADB, reboot, reconnect, writer import, token persistence or
activation request. Default is PLAN_ONLY. The caller owns physical readiness,
authenticated non-PTY transport and contemporaneous battery/thermal evidence.
"""
import argparse
import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import socket
import struct
import time

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT.parent / '2026-11-06-asus-stock-only-ram-rescue-build'
MANIFEST = '605cdec038dafe3dddabfe92b8bd6cd189734f740230dfc362d02a43421e4e47'
P10 = '3f99c785cca60bf56c2505711e2d26b72623daf28180515d44c5ba2abf03a44a'
PINS = {
    'artifacts/candidate/UNAPPROVED-STOCK-ONLY.img': '5a61d3d65a7ba6b29745a965d9911ab4483c951a0327339839a0541bcb9ab30f',
    'artifacts/original-stock.manifest': MANIFEST,
    'source/rescue.c': '23b0af1a8c813ae925459bf4614f768a5f90e5a76efb49bf8523135159c72c49',
    'source/common.h': '90fe60e79b3cc3932dab7e824bc803bb18ba086ea079beca8298c34ccf2a53c3',
}
REQUEST = b'RSC1' + struct.pack('<II', 2, 68) + bytes.fromhex(MANIFEST) + bytes.fromhex(P10) + struct.pack('<I', 1)
PARTITION_READ_BYTES = 3_753_902_080 + 16_740_352 + 2 * 16_740_352


def check_inputs():
    for name, expected in PINS.items():
        path = BUILD / name
        if path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError('Fixed input changed: ' + name)


def measure(stream, seconds):
    """Consume a fresh owned socket; send exactly one opcode2 request."""
    def limit():
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError('Whole measurement deadline expired; no retry')
        stream.settimeout(remaining)

    def read_exact(count):
        data = bytearray()
        while len(data) < count:
            limit()
            part = stream.recv(count - len(data))
            if not part:
                raise EOFError('Transport closed; no reconnect')
            data.extend(part)
        return bytes(data)

    try:
        if not math.isfinite(seconds) or not 0 < seconds <= 600:
            raise ValueError('Deadline must be finite, positive and at most 600 seconds')
        started = time.monotonic()
        deadline = started + seconds
        limit()
        stream.sendall(REQUEST)
        header = read_exact(12)
        magic, opcode, length = struct.unpack('<4sII', header)
        if magic != b'RSC1' or (opcode, length) != (0x82, 48):
            raise ValueError('Expected exact fixed 48-byte BOOT reconciliation reply')
        body = read_exact(48)
        if body[32:] != bytes([1]) * 16:
            raise ValueError('Original BOOT chunk bitmap does not match completely')
        limit()
        elapsed = time.monotonic() - started
        # Discard the token in body[:32]. Never send opcode3 or persist it.
        return {
            'result': 'OBSERVED_MATCH',
            'elapsed_seconds': elapsed,
            'matching_boot_chunks': 16,
            'source_derived_partition_read_bytes': PARTITION_READ_BYTES,
            'read_volume_excludes': 'CID/GPT identity checks and protocol overhead',
            'wire_request_count': 1,
            'wire_opcode': 2,
            'manifest_sha256': MANIFEST,
            'expected_current_p10_sha256': P10,
            'partition_write_requested': False,
            'whole_restore_timing_qualified': False,
            'physical_GO': False,
        }
    finally:
        stream.close()


def append(log, value):
    log.write(json.dumps(value, sort_keys=True) + '\n')
    log.flush()
    os.fsync(log.fileno())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--fd', type=int, help='Fresh owned connected AF_UNIX socket FD from parent transport')
    parser.add_argument('--seconds', type=float, default=180)
    parser.add_argument('--evidence', type=Path)
    args = parser.parse_args()
    if not args.execute:
        print(json.dumps({'mode': 'PLAN_ONLY', 'opcode': 2, 'image_index': 1,
                          'read_bytes_excluding_identity': PARTITION_READ_BYTES,
                          'requires': 'Commissioned exact rescue boot and parent authenticated stream',
                          'opens_transport': False, 'physical_GO': False}))
        return
    if args.fd is None or args.fd < 3 or args.evidence is None:
        parser.error('Execute requires an inherited fresh socket FD >=3 and new evidence file')
    if not math.isfinite(args.seconds) or not 0 < args.seconds <= 600:
        parser.error('Seconds must be finite, positive and at most 600')
    check_inputs()
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
    fd = os.open(args.evidence, flags, 0o600)
    with os.fdopen(fd, 'w') as log:
        append(log, {'result': 'UNKNOWN', 'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                     'deadline_seconds': args.seconds, 'pins': PINS,
                     'physical_GO': False, 'automatic_retry': False})
        parent = os.open(args.evidence.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(parent)
        finally:
            os.close(parent)
        stream = socket.socket(fileno=args.fd)
        try:
            if stream.family != socket.AF_UNIX or stream.type != socket.SOCK_STREAM:
                raise ValueError('Expected parent-owned AF_UNIX stream')
            stream.getpeername()
            result = measure(stream, args.seconds)
            append(log, result)
        except BaseException as error:
            stream.close()
            append(log, {'result': 'UNKNOWN', 'error_type': type(error).__name__,
                         'error': str(error), 'automatic_retry': False, 'physical_GO': False})
            raise
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
