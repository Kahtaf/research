#!/usr/bin/env python3
"""Bounded full stock-system backup. No transport is launched without --execute."""
from __future__ import annotations
import argparse
import base64
import zlib
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import selectors
import shlex
import shutil
import subprocess
import sys
import time
from policy import (SERIAL, ENDPOINT, TRANSPORT, FINGERPRINT, BLOCK, ALIAS, SIZE, CHUNK, BUFFER, TARGET,
                    REMOTE_BASE, Stop, require, sha, encoded, valid_run, digest_file,
                    private, ancestors, create_file, chunk_layout, validate_manifest, fsync_dir, CONSTRUCTION, validate_rows)
from health import healthy as health_snapshot

SPIKE = Path(__file__).resolve().parents[1]
WORKSPACE = SPIKE.parent
HELPER = SPIKE / 'scripts/root_shell_batched.py'
HELPER_HASH = '9dd219d06fcfb761ba5b7134c458215e3d93eb3cf0f13a64a199a2c2f4c7f39e'
ROOT_BINARY = WORKSPACE / '2026-11-05-asus-root-hardware-validation/sources/mtk-su-mirror-b'
ROOT_BINARY_HASH = '328632e853ff6427af9f35cb83a91d9e960f35d01188ee66d46ae9c7ce7c7827'
BASE = '/data/local/tmp/asus-stock-system-continuation'
ADB = ['adb', '-s', ENDPOINT]
SSH = ['ssh', '-T', '-i', str(Path.home() / '.ssh/asus_p00a_android17'),
       '-o', 'IdentitiesOnly=yes', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15',
       '-o', 'StrictHostKeyChecking=yes', '-o', 'HostKeyAlias=compute.8549823276971553556',
       '-o', 'UserKnownHostsFile=' + str(Path.home() / '.ssh/google_compute_known_hosts'),
       '-o', 'ServerAliveInterval=15', '-o', 'ServerAliveCountMax=2',
       'android@IP_REDACTED']
PROPS = {'ro.serialno': SERIAL, 'ro.product.device': 'P00A_2', 'ro.build.version.sdk': '24',
         'ro.build.fingerprint': FINGERPRINT, 'ro.adb.secure': '1', 'sys.boot_completed': '1'}

PARENT_PATH_GUARD = '''[ ! -L /data ]
[ ! -L /data/local ]
[ ! -L /data/local/tmp ]
[ -d /data ]
[ -d /data/local ]
[ -d /data/local/tmp ]
[ "$(stat -c '%u:%g:%a' /data)" = 1000:1000:771 ]
[ "$(stat -c '%u:%g:%a' /data/local)" = 0:0:751 ]
[ "$(stat -c '%u:%g:%a' /data/local/tmp)" = 2000:2000:771 ]'''

NODE_GUARD = f'''listing=$(ls -ln {BLOCK})
set -- $listing
[ "$#" -eq 9 ]
[ "$5" = 179, ]
[ "$6" = 25 ]
[ "$9" = {BLOCK} ]'''
MOUNT_GUARD = f'''system_mounts=0
while read source point fs options rest; do
    if [ "$point" = /system ]; then
        [ "$(readlink -f "$source")" = {BLOCK} ]
        [ "$fs" = ext4 ]
        case ",$options," in *,ro,*) ;; *) exit 81 ;; esac
        case ",$options," in *,rw,*) exit 82 ;; esac
        system_mounts=$((system_mounts + 1))
    fi
done < /proc/mounts
[ "$system_mounts" -eq 1 ]
system_mounts=0
while read mid parent dev fsroot point options rest; do
    if [ "$dev" = 179:25 ]; then
        case ",$options," in *,ro,*) ;; *) exit 83 ;; esac
        case ",$options," in *,rw,*) exit 84 ;; esac
        if [ "$point" = /system ]; then
            [ "$fsroot" = / ]
            system_mounts=$((system_mounts + 1))
        fi
    fi
done < /proc/self/mountinfo
[ "$system_mounts" -eq 1 ]'''
DEVICE_GUARD = '\n'.join(f'[ "$(getprop {k})" = {shlex.quote(v)} ]' for k, v in PROPS.items()) + f'''
[ "$(id -u)" = 0 ]
[ "$(readlink -f /data/local/tmp)" = /data/local/tmp ]
[ -b {BLOCK} ]
[ "$(readlink -f {BLOCK})" = {BLOCK} ]
[ "$(readlink -f {ALIAS})" = {BLOCK} ]
[ "$(cat /sys/class/block/mmcblk0p25/partition)" = 25 ]
[ "$(cat /sys/class/block/mmcblk0p25/start)" = 1072424 ]
[ "$(cat /sys/class/block/mmcblk0p25/size)" = 7331840 ]
[ "$(cat /sys/class/block/mmcblk0p25/dev)" = 179:25 ]
[ "$(cat /sys/class/block/mmcblk0/queue/logical_block_size)" = 512 ]
{NODE_GUARD}
{MOUNT_GUARD}'''


def directory_guard(canonical=True, base=BASE):
    prefix = '' if canonical else PARENT_PATH_GUARD + '\n'
    resolved = f'[ "$(readlink -f {base})" = {base} ]\n' if canonical else ''
    return prefix + f'''[ ! -L {base} ]
[ -d {base} ]
{resolved}[ "$(stat -c '%u:%g:%a' {base})" = 2000:2000:700 ]'''


def file_guard(path, size, inode=None, owner='2000:2000:600'):
    s = f'''[ ! -L {path} ]
[ -f {path} ]
[ "$(stat -c '%u:%g:%a' {path})" = {owner} ]
[ "$(stat -c '%h' {path})" = 1 ]
[ "$(stat -c '%s' {path})" = {size} ]'''
    if inode is not None:
        require(type(inode) is int and inode > 0, 'Invalid stage inode')
        s += f'\n[ "$(stat -c \'%i\' {path})" = {inode} ]'
    return s


def root_envelope(body, token):
    require(re.fullmatch('[0-9a-f]{32}', token) is not None, 'Invalid operation nonce')
    return f'''(
set -eu
umask 077
{DEVICE_GUARD}
{body}
)
asus_operation_rc=$?
printf '\\nASUS_SYSTEM_RC_{token}=%s\\n' "$asus_operation_rc"
exit 0
'''


def root_status(result, token):
    matches = re.findall(r'^ASUS_SYSTEM_RC_' + token + r'=(\d{1,3})\r?$', result.stdout, re.M)
    require(result.returncode == 0 and len(matches) == 1 and 0 <= int(matches[0]) <= 255,
            'Uncertain root/helper completion; no retry or cleanup')
    require(int(matches[0]) == 0, 'Root operation failed status ' + matches[0] + '; preserve stage')


def local_inputs():
    for path, expected in ((HELPER, HELPER_HASH), (ROOT_BINARY, ROOT_BINARY_HASH)):
        require(path.is_file() and not path.is_symlink() and digest_file(path)[1] == expected,
                'Immutable root dependency mismatch: ' + str(path))
    layout = json.loads((WORKSPACE / '2026-11-05-asus-latest-android-feasibility/evidence/live-partition-layout.json').read_text())
    system = [r for r in layout if r['name'] == 'system']
    require(len(system) == 1 and (system[0]['start_sector'], system[0]['sectors'], system[0]['size_bytes'])
            == (1072424, 7331840, SIZE), 'Historical layout mismatch (fresh guards still mandatory)')
    return {p.name: digest_file(p)[1] for p in sorted((SPIKE / 'source').glob('*.py'))}


class Journal:
    def __init__(self, directory):
        self.directory = directory
        self.sequence = 0
    def event(self, kind, **fields):
        self.sequence += 1
        raw = encoded(dict(at=dt.datetime.now(dt.timezone.utc).isoformat(), kind=kind, **fields))
        create_file(self.directory / ('%05d-%s.json' % (self.sequence, kind)), raw)
        fsync_dir(self.directory)
        return sha(raw)


def stream_process(argv, length, consume, timeout=180, popen=subprocess.Popen):
    """Drain binary stdout and bounded stderr concurrently; no text conversion/pipeline.

    consume sees <=1MiB at a time; overflow is refused before reaching it. Kill and
    reap only the local client on errors; remote/device state remains uncertain.
    """
    p = popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.DEVNULL)
    n, err = 0, bytearray()
    selector = selectors.DefaultSelector()
    selector.register(p.stdout, selectors.EVENT_READ, 'stdout')
    selector.register(p.stderr, selectors.EVENT_READ, 'stderr')
    deadline = time.monotonic() + timeout
    try:
        while selector.get_map():
            remaining = deadline - time.monotonic()
            require(remaining > 0, 'Binary transport timeout; stage uncertain')
            for key, _ in selector.select(min(remaining, 1)):
                b = os.read(key.fileobj.fileno(), BUFFER)
                if not b:
                    selector.unregister(key.fileobj)
                    continue
                if key.data == 'stdout':
                    n += len(b)
                    require(n <= length, 'Oversized binary transfer')
                    consume(b)
                else:
                    require(len(err) + len(b) <= BUFFER, 'Excessive transport diagnostics')
                    err.extend(b)
        rc = p.wait(timeout=max(0.01, deadline-time.monotonic()))
        require(rc == 0 and n == length, f'Binary transport failed/short: status={rc}, bytes={n}, expected={length}; ' + err.decode('utf-8', 'replace'))
        return n
    except BaseException:
        p.kill()
        p.wait()
        raise
    finally:
        selector.close()
        p.stdout.close()
        p.stderr.close()


class Device:
    def __init__(self, run, journal):
        self.run, self.journal = valid_run(run), journal
        self.base = BASE + "/" + self.run
        self.inodes = {}
        self.size = None
    def command(self, argv, script=None, timeout=95):
        self.journal.event('dispatch', argv=argv, script=script)
        try:
            result = subprocess.run(argv, input=script, text=True, capture_output=True, timeout=timeout)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise Stop('Command uncertain; stop without cleanup') from exc
        self.journal.event('returned', status=result.returncode, stdout=result.stdout, stderr=result.stderr)
        require(result.returncode == 0, 'Command failed; no retry')
        return result
    def healthy(self):
        return health_snapshot(self.journal.event)
    def root(self, body):
        local_inputs()
        self.healthy()
        # Immutable helper pushes this path before gaining root. Refuse symlinks,
        # alien ownership and writable ancestors BEFORE invoking that helper.
        self.command(ADB + ['shell', f'''set -eu
{PARENT_PATH_GUARD}
p=/data/local/tmp/asus-continuation-mtk-su64
[ ! -L "$p" ]
if [ -e "$p" ]; then
[ -f "$p" ]
[ "$(stat -c '%u:%g:%a:%h' "$p")" = 2000:2000:700:1 ]
fi'''])
        token = secrets.token_hex(16)
        result = self.command([sys.executable, str(HELPER)], root_envelope(body, token), timeout=300)
        root_status(result, token)
        self.healthy()
        return result.stdout
    def stage_guard(self):
        return directory_guard() + "\n" + directory_guard(base=self.base) + '\n' + file_guard(self.base+'/owner', len(self.run), owner='0:0:600') + f'\n[ "$(cat {self.base}/owner)" = {self.run} ]'
    def preflight(self):
        self.root(f'''{PARENT_PATH_GUARD}
if [ -e {BASE} ] || [ -L {BASE} ]; then
{directory_guard()}
fi
[ ! -e {self.base} ]
[ ! -L {self.base} ]
data_free=
rows=$(df -k /data)
while read filesystem blocks used available rest; do
    case "$available" in ''|*[!0-9]*) ;; *) data_free=$available ;; esac
done <<EOF
$rows
EOF
[ -n "$data_free" ]
[ "$data_free" -ge 131072 ]''')
    def setup(self):
        self.root(f'''{PARENT_PATH_GUARD}
if [ ! -e {BASE} ] && [ ! -L {BASE} ]; then
mkdir {BASE}
chmod 700 {BASE}
chown 2000:2000 {BASE}
fi
{directory_guard()}
[ ! -e {self.base} ]
[ ! -L {self.base} ]
mkdir {self.base}
chmod 700 {self.base}
chown 2000:2000 {self.base}
{directory_guard(base=self.base)}
set -C
printf '%s' {self.run} > {self.base}/owner
{self.stage_guard()}''')
    def stage(self, label, offset, length):
        require(label in ('a', 'b') and offset % BUFFER == 0 and length % BUFFER == 0
                and (offset, length) in [(o, n) for _, o, n in chunk_layout()], 'Invalid fixed system slice')
        f = self.base + '/' + label + '.bin'
        out = self.root(f'''{self.stage_guard()}
[ ! -e {f} ]
[ ! -L {f} ]
dd if={BLOCK} of={f} bs={BUFFER} skip={offset//BUFFER} count={length//BUFFER}
{DEVICE_GUARD}
chmod 600 {f}
chown 2000:2000 {f}
{file_guard(f, length)}
printf '\\nASUS_STAGE_INODE='; stat -c '%i' {f}''')
        ids = re.findall(r'^ASUS_STAGE_INODE=(\d+)\r?$', out, re.M)
        require(len(ids) == 1, 'Stage inode missing/ambiguous')
        self.inodes[label] = int(ids[0])
        self.size = length
        self.journal.event('source_read_staged', label=label, offset=offset, bytes=length, inode=int(ids[0]))
    def binary(self, label, length, consume):
        require(label in self.inodes and length == self.size, 'Unrecorded stage')
        features = self.command(ADB + ['features']).stdout.splitlines()
        require('shell_v2' in features, 'Authenticated device must advertise shell_v2 for binary transfer')
        f = self.base + '/' + label + '.bin'
        script = 'set -eu\n' + directory_guard(canonical=False) + "\n" + directory_guard(canonical=False, base=self.base) + '\n' + file_guard(f, length, self.inodes[label]) + '\ncat ' + f
        self.journal.event('binary_dispatch', label=label, bytes=length)
        n = stream_process(ADB + ['shell', '-T', script], length, consume)
        self.journal.event('binary_received', label=label, bytes=n)
    def clean_chunk(self):
        require(set(self.inodes) == {'a', 'b'}, 'Cannot clean unverified/incomplete stage')
        guards = '\n'.join(file_guard(self.base+'/'+label+'.bin', self.size, inode) for label, inode in self.inodes.items())
        self.root(self.stage_guard() + '\n' + guards + f'\nrm {self.base}/a.bin {self.base}/b.bin\n[ ! -e {self.base}/a.bin ]\n[ ! -e {self.base}/b.bin ]')
        self.inodes.clear()
        self.journal.event('device_chunk_cleaned')
    def finish(self):
        require(not self.inodes, 'Outstanding device stage')
        self.root(self.stage_guard() + f'\nrm {self.base}/owner\nrmdir {self.base}\n[ ! -e {self.base} ]\n[ ! -L {self.base} ]')
        self.journal.event('device_stage_removed')


def validate_root_request(script):
    """The helper accepts only this coordinator's exact fixed-scope templates.

    Rendering uses a replacement root method and a no-op journal; it performs
    no I/O. This also prevents standalone helper stdin from becoming an
    arbitrary root command interface.
    """
    runs = set(re.findall(re.escape(BASE)+r'/([0-9]{8}T[0-9]{6}Z-[0-9a-f]{16})', script))
    tokens = re.findall(r'ASUS_SYSTEM_RC_([0-9a-f]{32})=', script)
    require(len(runs) == len(tokens) == 1, 'Invalid fixed root request envelope')
    run, token = runs.pop(), tokens[0]
    bodies = []
    journal = type('RenderOnly', (), {'event': lambda *a, **k: None})()
    device = Device(run, journal)
    def render(body):
        bodies.append(body)
        return 'ASUS_STAGE_INODE=1\n'
    device.root = render
    device.preflight()
    device.setup()
    device.finish()
    reads = re.findall(r'dd if=(\S+) of=(\S+) bs=(\d+) skip=(\d+) count=(\d+)', script)
    if len(reads) == 1:
        src, dst, bs, skip, count = reads[0]
        if src == BLOCK and int(bs) == BUFFER and dst in (device.base+'/a.bin', device.base+'/b.bin'):
            offset, length = int(skip)*BUFFER, int(count)*BUFFER
            if (offset, length) in [(o,n) for _,o,n in chunk_layout()]:
                device.stage(dst[-5], offset, length)
    if not reads:
        inodes, lengths = {}, []
        for label in ('a','b'):
            f = re.escape(device.base+'/'+label+'.bin')
            inode = re.findall(r"\[ \"\$\(stat -c '%i' "+f+r"\)\" = (\d+) \]", script)
            length = re.findall(r"\[ \"\$\(stat -c '%s' "+f+r"\)\" = (\d+) \]", script)
            if len(inode) == len(length) == 1:
                inodes[label] = int(inode[0])
                lengths.append(int(length[0]))
        if set(inodes) == {'a','b'} and len(set(lengths)) == 1 and lengths[0] in {n for _,_,n in chunk_layout()}:
            device.inodes, device.size = inodes, lengths[0]
            device.clean_chunk()
    require(any(script == root_envelope(body, token) for body in bodies), 'Helper refuses non-template root command')


def pack_request(request):
    raw = json.dumps(request, separators=(',', ':')).encode()
    require(len(raw) <= 1024*1024, 'Remote metadata request too large')
    return base64.b64encode(zlib.compress(raw)).decode('ascii')

REQUEST_BOOTSTRAP = """import sys,types,base64,zlib
packed = base64.b64decode(sys.argv[1], validate=True)
decoder = zlib.decompressobj()
request = decoder.decompress(packed, 1024*1024+1)
if len(request) > 1024*1024 or not decoder.eof or decoder.unused_data or decoder.unconsumed_tail:
    raise ValueError('Invalid/oversized packed metadata request')
sys.argv[1] = request.decode('utf-8')
"""


class Remote:
    def __init__(self, run, journal):
        self.run, self.journal = run, journal
        # Source is sent as quoted command argument, not confused with binary stdin.
        policy = (SPIKE/'source/policy.py').read_text()
        worker = (SPIKE/'source/remote_worker.py').read_text()
        self.code = REQUEST_BOOTSTRAP + 'm=types.ModuleType("policy")\nsys.modules["policy"]=m\nexec(' + repr(policy) + ',m.__dict__)\nexec(' + repr(worker) + ')\n'
    def call(self, operation, file=None, **fields):
        q = dict(operation=operation, run=self.run, **fields)
        self.journal.event('remote_dispatch', request=q)
        command = shlex.join(['python3', '-c', self.code, pack_request(q)])
        require(len(command.encode()) < 65536, 'Remote command exceeds bounded argv budget')
        argv = SSH + [command]
        try:
            result = subprocess.run(argv, stdin=file if file else subprocess.DEVNULL,
                                    capture_output=True, timeout=900)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise Stop('SSH state uncertain; do not retry') from exc
        self.journal.event('remote_returned', status=result.returncode,
                           stdout=result.stdout.decode('utf-8', 'replace'), stderr=result.stderr.decode('utf-8', 'replace'))
        require(result.returncode == 0, 'Remote operation failed; preserve files')
        answer = json.loads(result.stdout)
        require(answer.get('run') == self.run and answer.get('operation') == operation, 'SSH response identity mismatch')
        return answer
    def put(self, index, path, length, digest):
        private(path)
        with path.open('rb') as f:
            r = self.call('put', file=f, index=index, bytes=length, sha256=digest)
        require((r.get('index'), r.get('bytes'), r.get('sha256')) == (index, length, digest), 'Remote chunk acknowledgement mismatch')
        return r['sha256']


def transfer(run, directory, device, remote, journal, code_hashes, inputs):
    """One 32MiB host file; second source read is compared as bounded binary stream."""
    rows = list(inputs["chunks"])
    validate_rows(rows)
    input_sha = sha(encoded(inputs))
    path = directory / 'chunk.bin'
    remote.call('begin')
    imported = remote.call('reuse', source_run=inputs['source_run'], chunks=rows, reviewed_input_sha256=input_sha)
    require(len(imported.get('receipts', [])) == len(rows), 'Missing prefix copy receipts')
    for row, receipt in zip(rows, imported['receipts']):
        require(receipt.get('index') == row['index'], 'Prefix receipt index mismatch')
        for side in ('source', 'copied'):
            require((receipt[side].get('bytes'), receipt[side].get('sha256')) == (row['bytes'], row['sha256_a']), 'Prefix copy acknowledgement mismatch')
    journal.event('prefix_verified', chunks=rows, source_run=inputs['source_run'], reviewed_input_sha256=input_sha)
    device.setup()
    for index, offset, length in chunk_layout()[len(rows):]:
        device.stage('a', offset, length)
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        ha = hashlib.sha256()
        with os.fdopen(fd, 'wb') as out:
            def first(b):
                out.write(b)
                ha.update(b)
            device.binary('a', length, first)
            out.flush()
            os.fsync(out.fileno())
        st = private(path)
        require(digest_file(path) == (length, ha.hexdigest()), 'Host file actual-byte verification failed')
        device.stage('b', offset, length)
        hb, compared = hashlib.sha256(), 0
        with path.open('rb') as first_file:
            def second(b):
                nonlocal compared
                require(first_file.read(len(b)) == b, 'Independent source reads differ')
                hb.update(b)
                compared += len(b)
            device.binary('b', length, second)
            require(not first_file.read(1), 'Second source read truncated')
        require(compared == length and ha.digest() == hb.digest(), 'Source chunk hash/length mismatch')
        receipt = journal.event('two_source_reads_verified', index=index, offset=offset, bytes=length,
                                sha256_a=ha.hexdigest(), sha256_b=hb.hexdigest(), compared_bytes=compared)
        origin = dict(run=run, transport=TRANSPORT, source_code_sha256=code_hashes,
                      helper_sha256=HELPER_HASH, root_binary_sha256=ROOT_BINARY_HASH, receipt_sha256=receipt)
        row = dict(index=index, offset=offset, bytes=length, sha256_a=ha.hexdigest(), sha256_b=hb.hexdigest(),
                   remote_sha256=ha.hexdigest(), source_capture=origin)
        journal.event('capture_ready_for_upload', row=row)
        rh = remote.put(index, path, length, ha.hexdigest())
        rows.append(row)
        journal.event('chunk_verified', **row)
        # These are the only payload deletion paths: after recorded remote readback.
        device.clean_chunk()
        now = private(path)
        require((now.st_dev, now.st_ino, now.st_size) == (st.st_dev, st.st_ino, length), 'Host stage replaced; refuse cleanup')
        require(digest_file(path) == (length, rh), 'Host stage changed; refuse cleanup')
        path.unlink()
        journal.event('host_chunk_cleaned', index=index)
    device.finish()
    assembly = remote.call('assemble', chunks=rows)
    require(assembly.get('bytes') == SIZE, 'Assembly acknowledgement length mismatch')
    m = dict(schema=2, run=run, target=TARGET, transport=TRANSPORT, bytes=SIZE,
             construction=CONSTRUCTION, assembled_sha256=assembly['sha256'], chunks=rows,
             reviewed_input_sha256=input_sha, source_code_sha256=code_hashes,
             helper_sha256=HELPER_HASH, root_binary_sha256=ROOT_BINARY_HASH,
             completed_at=dt.datetime.now(dt.timezone.utc).isoformat())
    validate_manifest(m, run)
    raw = encoded(m)
    create_file(directory/'manifest.json', raw)
    fsync_dir(directory)
    expected = dict(run=run, bytes=SIZE, sha256=m['assembled_sha256'], manifest_sha256=sha(raw))
    final = remote.call('finalize', manifest=m, manifest_sha256=sha(raw))
    require({k: final.get(k) for k in expected} == expected, 'Remote final acknowledgement mismatch')
    verified = remote.call('verify', manifest_sha256=sha(raw))
    require({k: verified.get(k) for k in expected} == expected, 'Remote final readback mismatch')
    create_file(directory/'COMPLETE.json', encoded(expected))
    journal.event('complete', **expected)
    return expected


def main(argv=None):
    from continuation import prepare, validate_input, LEGACY_RUN, safe_bytes
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare', 'backup', 'preflight', 'verify'], nargs='?', default='backup')
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--exclusive-device-owner', action='store_true')
    parser.add_argument('--reviewed-inputs', action='store_true', help='Parent reviewed chosen capture evidence and source pins')
    parser.add_argument('--stock-unchanged-since-capture', action='store_true')
    parser.add_argument('--run-id')
    parser.add_argument('--from-run', default=LEGACY_RUN, help='Fixed legacy run or prior run within this spike only')
    parser.add_argument('--include-uncertain-last-put', action='store_true', help='Inspect next completed double capture; remote missing/partial bytes still fail')
    parser.add_argument('--input-sha256')
    parser.add_argument('--manifest-sha256')
    args = parser.parse_args(argv)
    os.umask(0o077)
    run = valid_run(args.run_id or (dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+secrets.token_hex(8)))
    code_hashes = local_inputs()
    inputs = None
    if args.action == 'prepare':
        require(not args.execute, 'Prepare is offline only')
        inputs = prepare(args.from_run, args.include_uncertain_last_put)
        raw = encoded(inputs)
        path = SPIKE/'evidence/inputs'/(sha(raw)+'.json')
        ancestors(path)
        private(path.parent, directory=True)
        if os.path.lexists(path):
            private(path)
            require(path.read_bytes() == raw, 'Input artifact collision')
        else:
            create_file(path, raw)
            fsync_dir(path.parent)
        print(json.dumps(dict(mode='OFFLINE_PREPARED', input_sha256=sha(raw), path=str(path),
                              prefix_chunks=len(inputs['chunks']), remaining_chunks=len(chunk_layout())-len(inputs['chunks'])), indent=2))
        return 0
    if args.action == 'verify':
        require(args.run_id and re.fullmatch('[0-9a-f]{64}', args.manifest_sha256 or ''), 'Verify requires run id and pinned manifest SHA256')
    else:
        if args.input_sha256:
            require(re.fullmatch('[0-9a-f]{64}', args.input_sha256), 'Invalid input SHA256')
            path = SPIKE/'evidence/inputs'/(args.input_sha256+'.json')
            private(path)
            inputs = validate_input(json.loads(safe_bytes(path)), args.input_sha256)
        else:
            inputs = prepare(args.from_run, args.include_uncertain_last_put)
        require(inputs['source_run'] != run, 'Destination must be a fresh run')
    plan = dict(mode='EXECUTE' if args.execute else 'PLAN_ONLY', action=args.action, run=run, target=TARGET,
                transport=TRANSPORT, device_temp_base=BASE+'/'+run,
                host_max_payload_bytes=CHUNK, device_max_payload_bytes=2*CHUNK,
                chunks=len(chunk_layout()), final_chunk_bytes=chunk_layout()[-1][2],
                remote_path=str(REMOTE_BASE/run), remote_peak_payload_bytes=2*SIZE,
                source_code_sha256=code_hashes, helper_sha256=HELPER_HASH, root_binary_sha256=ROOT_BINARY_HASH,
                prefix_chunks=len(inputs['chunks']) if inputs else None,
                reviewed_input_sha256=sha(encoded(inputs)) if inputs else None,
                resumable='explicit-new-run-with-reviewed-evidence-and-actual-byte-verification', no_raw_block_writes=True)
    if not args.execute:
        print(json.dumps(plan, indent=2))
        return 0
    require(args.exclusive_device_owner, 'Execution requires exclusive parent ownership of device and backup runs')
    if args.action != 'verify':
        require(args.input_sha256 and args.reviewed_inputs and args.stock_unchanged_since_capture,
                'Execution requires pinned reviewed inputs and unchanged-stock attestation')
    root = SPIKE/'evidence/runs'
    ancestors(root)
    private(root, directory=True)
    directory = root / (run if args.action == 'backup' else run+'-'+args.action+'-'+secrets.token_hex(4))
    directory.mkdir(mode=0o700)
    journal = Journal(directory)
    journal.event('plan', **plan)
    if inputs:
        create_file(directory/'input.json', encoded(inputs))
        fsync_dir(directory)
    lockpath = root/'device.lock'
    fd = os.open(lockpath, os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'r+') as lock:
        private(lockpath)
        fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB)
        try:
            remote = Remote(run, journal)
            if args.action == 'verify':
                path = root/run/'manifest.json'
                private(path)
                raw = safe_bytes(path)
                require(sha(raw) == args.manifest_sha256, 'Pinned local manifest mismatch')
                manifest = json.loads(raw)
                validate_manifest(manifest, run)
                result = remote.call('verify', manifest_sha256=args.manifest_sha256)
                expected = dict(run=run, bytes=SIZE, sha256=manifest['assembled_sha256'], manifest_sha256=args.manifest_sha256)
                require({k: result.get(k) for k in expected} == expected, 'Final verification acknowledgement mismatch')
                create_file(directory/'VERIFIED.json', encoded(expected))
                fsync_dir(directory)
            else:
                require(shutil.disk_usage(directory).free >= 128*1024*1024, 'Need 128MiB free host space')
                device = Device(run, journal)
                remote.call('preflight')
                device.preflight()
                result = (dict(outcome='preflight_passed', run=run) if args.action == 'preflight'
                          else transfer(run, directory, device, remote, journal, code_hashes, inputs))
            print(json.dumps(result, indent=2))
            return 0
        except BaseException as exc:
            journal.event('STOP_preserve_all_staging', error=type(exc).__name__+': '+str(exc))
            raise


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (Stop, OSError, ValueError, subprocess.SubprocessError) as exc:
        print('STOP: '+str(exc), file=sys.stderr)
        raise SystemExit(2)
