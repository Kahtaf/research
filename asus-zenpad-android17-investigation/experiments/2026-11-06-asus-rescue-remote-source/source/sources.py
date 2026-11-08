"""Bounded host readers. Only RemoteSource launches SSH, never a target process."""
import base64
import hashlib
import json
import os
from pathlib import Path
import shlex
import stat
import subprocess
import worker

ROOT = Path(__file__).resolve().parents[1]


def reference(key):
    profile = dict(worker.FIXED_PROFILES[key])
    chunks = (ROOT / 'profiles' / (key + '.chunks')).read_bytes()
    if (len(chunks) != profile['count'] * 32
            or hashlib.sha256(chunks).hexdigest() != profile['chunks_sha256']):
        raise ValueError('pinned compact chunk export changed')
    return profile, chunks


def ssh_command(key):
    if key not in worker.FIXED_PROFILES:
        raise ValueError('unknown/unbound source profile')
    # Only locally shipped source and enum profile keys enter this fixed command.
    code = base64.b64encode((ROOT / 'source/worker.py').read_bytes()).decode('ascii')
    bootstrap = 'import base64;exec(compile(base64.b64decode("' + code + '"),"fixed-source-worker","exec"))'
    command = 'python3 -B -c ' + shlex.quote(bootstrap) + ' ' + shlex.quote(key)
    home = Path.home()
    return ['ssh', '-F', '/dev/null', '-T', '-i', str(home / '.ssh/asus_p00a_android17'),
            '-o', 'IdentitiesOnly=yes', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15',
            '-o', 'StrictHostKeyChecking=yes', '-o', 'HostKeyAlias=compute.8549823276971553556',
            '-o', 'UserKnownHostsFile=' + str(home / '.ssh/google_compute_known_hosts'),
            '-o', 'ForwardAgent=no', '-o', 'ClearAllForwardings=yes', '-o', 'ControlMaster=no',
            '-o', 'ControlPath=none', '-o', 'ServerAliveInterval=15', '-o', 'ServerAliveCountMax=2',
            'android@IP_REDACTED', command]


class RemoteSource:
    def __init__(self, key):
        self.key = key
        self.profile, self.chunks = reference(key)
        self.process = None
        self.verified = False
        self.dead = False
        self.consumed = False
        self.next_index = 0

    def open(self):
        if self.process is not None or self.dead:
            raise ValueError('source session cannot reopen')
        self.process = subprocess.Popen(ssh_command(self.key), stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=0)
        try:
            _, reply = worker.receive(self.process.stdout, 0x80, limit=4096)
            hello = json.loads(reply)
            if set(hello) != {'stat', 'profile'} or hello['profile'] != self.profile:
                raise ValueError('source identity/profile mismatch')
            self.stat = hello['stat']
            if not isinstance(self.stat, list) or len(self.stat) != 9 or not all(type(v) is int for v in self.stat):
                raise ValueError('invalid held source stat')
            if (self.stat[0] < 0 or self.stat[1] <= 0
                    or self.stat[2] != stat.S_IFREG | self.profile['mode']
                    or self.stat[3:7] != [self.profile['uid'], self.profile['gid'], 1, self.profile['size']]):
                raise ValueError('held source stat/profile guard mismatch')
        except BaseException:
            self.dead = True
            self.close()
            raise
        return self

    def exchange(self, op, payload=b'', limit=worker.CHUNK + worker.REPLY.size):
        if self.dead or self.process is None:
            raise ValueError('source session unavailable')
        try:
            worker.send(self.process.stdin, op, payload)
            _, data = worker.receive(self.process.stdout, op + 0x80, limit=limit)
            return data
        except BaseException:
            self.dead = True
            raise

    def preflight(self):
        if self.verified or self.consumed:
            raise ValueError('fresh source preflight required')
        data = self.exchange(1, limit=32 + worker.MAX_CHUNKS * 32)
        if data != bytes.fromhex(self.profile['sha256']) + self.chunks:
            self.dead = True
            raise ValueError('source whole/chunk preflight mismatch')
        self.verified = True
        self.check()
        return data[:32], data[32:]

    def check(self):
        if self.exchange(4, limit=0) != b'':
            raise ValueError('source stat check')

    def read_chunk(self, index, sample=False):
        if type(index) is not int or not 0 <= index < self.profile['count']:
            raise ValueError('host source index')
        if not sample and (not self.verified or index != self.next_index):
            raise ValueError('preflight/sequential source required')
        offset = index * worker.CHUNK
        length = min(worker.CHUNK, self.profile['size'] - offset)
        reply = self.exchange(3 if sample else 2, worker.REQUEST.pack(index, offset, length),
                              limit=worker.REPLY.size + length)
        try:
            if len(reply) != worker.REPLY.size + length:
                raise ValueError('source reply short/length')
            got_index, got_offset, got_length, digest = worker.REPLY.unpack_from(reply)
            data = reply[worker.REPLY.size:]
            expected = self.chunks[index * 32:(index + 1) * 32]
            if ((got_index, got_offset, got_length) != (index, offset, length)
                    or digest != expected or hashlib.sha256(data).digest() != expected):
                raise ValueError('source reply index/position/digest/data')
            if index == 0 and data[:4] == bytes.fromhex('3aff26ed'):
                raise ValueError('Android sparse encoded source')
            if not sample:
                self.next_index += 1
            return data
        except BaseException:
            self.dead = True
            raise

    def receipt(self):
        if not self.verified or self.dead:
            raise ValueError('SOURCE receipt requires actual full held-FD preflight')
        return {'format': 'SOURCE1', 'scope': 'source-only', 'target_authorized': False,
                'profile_key': self.key, 'profile': self.profile, 'stat': self.stat,
                'full_preflight': True, 'session_reuse': False,
                'chunk_export_sha256': hashlib.sha256(self.chunks).hexdigest()}

    def close(self):
        proc = self.process
        self.dead = True
        if proc is not None:
            if proc.stdin and not proc.stdin.closed:
                proc.stdin.close()
            if proc.stdout and not proc.stdout.closed:
                proc.stdout.close()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()


class LocalSource:
    """The parent may use the existing stock bundle without any extra copy."""
    def __init__(self, profile):
        self.profile = dict(profile)
        self.raw = worker.HeldRaw(profile)
        self.verified = False
        self.consumed = False
        self.next_index = 0

    def preflight(self):
        result = self.raw.preflight()
        self.verified = True
        return result

    def check(self):
        self.raw.check()

    def read_chunk(self, index):
        if index != self.next_index:
            raise ValueError('local source order')
        data = self.raw.chunk(index)
        self.next_index += 1
        return data

    def close(self):
        self.raw.close()

LOCAL_PROFILES = {'stock-system': {'role': 0, 'path': '/OWNER_HOME/Documents/workspace/ideas/2026-11-06-asus-local-stock-rollback/artifacts/stock-rollback/system.img', 'size': 3753902080, 'sha256': '4597a7b5a9f30f9e851f1ae71b54a2db1845465e36a1a55b70ae26e171d5cd49', 'uid': 501, 'gid': 20, 'mode': 256, 'nlink': 1, 'chunk_bytes': 1048576, 'count': 3580, 'chunks_sha256': '994b427a2ded325bceb26bda24fea8bf524d5dda432fb1354a11c898b87d2fc8'}, 'stock-boot': {'role': 1, 'path': '/OWNER_HOME/Documents/workspace/ideas/2026-11-06-asus-local-stock-rollback/artifacts/stock-rollback/boot.img', 'size': 16740352, 'sha256': '7bb68511b1ade34d24c3e932da7260e6753fa87270bd8249a7218755a5df3316', 'uid': 501, 'gid': 20, 'mode': 256, 'nlink': 1, 'chunk_bytes': 1048576, 'count': 16, 'chunks_sha256': 'cdf9a2c22e01774b0cf6f20591e41d964bc7b5c5890117592c03a71432861a37'}}

def local_source(path):
    for profile in LOCAL_PROFILES.values():
        if str(path) == profile["path"]:
            return LocalSource(profile)
    raise ValueError("unbound local source; only fixed original stock bundle admitted")
