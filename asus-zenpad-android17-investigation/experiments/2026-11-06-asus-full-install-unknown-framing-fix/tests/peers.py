"""Finite owned fake children. Never imports transport launch/admission code."""
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import struct
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'source'))
resource.setrlimit(resource.RLIMIT_CPU, (5, 5))
signal.alarm(5)
try:
    resource.setrlimit(resource.RLIMIT_DATA, (256 * 1024**2, 256 * 1024**2))
except (ValueError, OSError):
    pass  # Darwin refuses this limit; finite fixtures and measured RSS are used.
import worker
from pinned import client as legacy


def record(path, data):
    with open(path, 'a') as out:
        out.write(json.dumps(data) + '\n')


def stall():
    time.sleep(2)  # Every fake is finite even if its parent fails.
    raise SystemExit(0)


def source(config):
    profile, fault, log = config['profile'], config['fault'], config['log']
    original_send = worker.send
    original_receive = worker.receive
    def receive(*args, **kw):
        result = original_receive(*args, **kw)
        record(log, {'source_op': result[0]})
        return result
    worker.receive = receive
    init = worker.HeldRaw.__init__
    def held(self, profile):
        init(self, profile)
        record(log, {'held_fd': self.fd, 'stat': self.initial})
    worker.HeldRaw.__init__ = held
    counter = [0]
    def send(stream, op, data=b''):
        record(log, {'source_reply': op})
        if op == 0x80 and fault in ('hello-profile','hello-stat'):
            hello=json.loads(data)
            if fault == 'hello-profile':hello['profile']['sha256']='0'*64
            else:hello['stat'][5]=2
            data=json.dumps(hello).encode()
        if op == 0x81 and fault == 'bad-chunks':data=data[:-1]+bytes([data[-1]^1])
        if op == 0x82 and fault == 'bad-chunk-digest':data=data[:16]+b'X'*32+data[48:]
        if op == 0x80 and fault == 'hello-header':
            stream.write(worker.HEADER.pack(b'SRC1', op, len(data))[:7]);stream.flush();stall()
        if op == 0x81:
            if fault == 'preflight-stall':
                stream.write(worker.HEADER.pack(b'SRC1', op, len(data)) + data[:8]);stream.flush();stall()
            if fault == 'source-drip':
                block = worker.HEADER.pack(b'SRC1', op, len(data)) + data
                for byte in block:
                    stream.write(bytes([byte]));stream.flush();time.sleep(.025)
                return
        if op == 0x82:
            counter[0] += 1
            if counter[0] == 2 and fault == 'chunk-stall':
                stream.write(worker.HEADER.pack(b'SRC1', op, len(data)) + data[:17]);stream.flush();stall()
        if fault == 'stderr':
            os.write(2, b'e' * 131072)
        original_send(stream, op, data)
        if op == 0x80 and fault == 'no-read':stall()
        if (op == 0x81 and fault == 'mutation') or (op == 0x82 and counter[0] == 1 and fault == 'mid-mutation'):
            path = Path(profile['path']);path.chmod(0o600)
            with path.open('r+b') as raw:raw.write(b'!')
            path.chmod(0o400)
    worker.send = send
    try:
        worker.serve(profile, sys.stdin.buffer, sys.stdout.buffer)
    except (EOFError, BrokenPipeError, ConnectionResetError, ValueError) as e:
        record(log, {'source_exit': type(e).__name__})


def target(config):
    manifest = bytes.fromhex(config['manifest'])
    row = legacy.parse(manifest)[0]
    expected = bytes.fromhex(config['data'])
    tail = b'PRESERVED-PARTITION-TAIL'
    actual = bytearray((expected[:worker.CHUNK] if config['skip'] else b'?' * worker.CHUNK)
                       + b'?' * (len(expected) - worker.CHUNK) + tail)
    index = 0
    fault, log = config['fault'], config['log']
    def reply(op, data=b''):
        frame = b'RSC1' + struct.pack('<II', op, len(data)) + data
        if (op == 0x84 and index == 0 and fault in ('partial-ack','ack-header','ack-drip')):
            if fault == 'ack-drip':
                for byte in frame:
                    os.write(1, bytes([byte]));time.sleep(.025)
                return
            os.write(1, frame[:8 if fault == 'ack-header' else 15]);stall()
        if op == 0x82 and fault == 'reconcile-stall':
            os.write(1, frame[:13]);stall()
        if op == 0x85 and fault == 'whole-stall':
            os.write(1, frame[:14]);stall()
        if fault == 'stderr':
            os.write(2, b't' * 131072)
        os.write(1, frame)
    try:
        while True:
            magic, op, size = struct.unpack('<4sII', legacy.readn(0, 12))
            data = legacy.readn(0, size)
            if magic != b'RSC1':raise ValueError('target magic')
            record(log, {'target_op': op})
            if op == 1:reply(0x81, b'fake idle')
            elif op in (2, 8):
                if data[:32] != hashlib.sha256(manifest).digest() or data[32:64] != b'P'*32:
                    raise ValueError('binding')
                if op == 8 and (len(data) != 104 or data[72:] != row['full']):raise ValueError('inverse')
                same = bytes(hashlib.sha256(actual[i:i+min(worker.CHUNK,row['size']-i)]).digest() == row['chunks'][(i//worker.CHUNK)*32:(i//worker.CHUNK+1)*32]
                             for i in range(0,row['size'],worker.CHUNK))
                reply(0x82, b'T'*32 + same)
            elif op == 3:
                if data != b'T'*32:raise ValueError('token')
                reply(0x83)
            elif op in (4, 7):
                offset = index * worker.CHUNK
                n = min(worker.CHUNK, row['size'] - offset)
                if op == 7:
                    if data or hashlib.sha256(actual[offset:offset+n]).digest() != row['chunks'][index*32:(index+1)*32]:raise ValueError('skip')
                else:
                    if len(data) != n or hashlib.sha256(data).digest() != row['chunks'][index*32:(index+1)*32]:raise ValueError('write')
                    actual[offset:offset+n] = data
                record(log, {'accepted_chunk':index,'matches':actual[:offset+n] == expected[:offset+n]})
                reply(0x84, struct.pack('<II', index + (1 if fault == 'wrong-ack' else 0), op == 7));index += 1
            elif op == 5:
                if actual[:row['size']] != expected or actual[row['size']:] != tail:raise ValueError('whole/tail')
                reply(0x85, row['full'] if fault != 'wrong-whole' else b'X'*32)
            elif op == 9:
                if data != row['full']:raise ValueError('commit')
                record(log, {'committed':True, 'tail_preserved':actual[row['size']:] == tail})
                if fault == 'lost-commit':stall()
                if fault == 'commit-exit':return
                reply(0x89, data)
            else:raise ValueError('unexpected opcode')
    except (EOFError, BrokenPipeError, ConnectionResetError):
        pass


if __name__ == '__main__':
    kind, path = sys.argv[1:]
    config = json.loads(Path(path).read_text())
    if kind == 'source':source(config)
    elif kind == 'target':target(config)
    elif kind == 'legacy-read':
        os.write(1,b'READY');legacy.receive(0,0x84)
    elif kind == 'legacy-write':
        os.write(1,b'READY');legacy.send(1,4,b'X'*worker.CHUNK)
    elif kind == 'features':
        os.write(2,b'e'*131072)
        os.write(1,b'shell_v2,cmd\n')
    elif kind == 'raw':
        os.write(1,b'READY')
        action=config['action']
        if action == 'exit':sys.exit(7)
        if action == 'silent':stall()
        if action == 'near':
            time.sleep(config['delay'])
            while os.read(0,65536):pass
        else:
            frame=b'RSC1'+struct.pack('<II',0x84,8)+struct.pack('<II',0,0)
            if action == 'partial-header':os.write(1,frame[:7]);stall()
            if action == 'partial-body':os.write(1,frame[:15]);stall()
            if action == 'drip':
                for byte in frame:os.write(1,bytes([byte]));time.sleep(.025)
            if action == 'stderr':os.write(2,b'e'*262144);os.write(1,frame)
            if action == 'tail-stderr':
                os.write(1,frame);os.write(2,b'e'*262144)
