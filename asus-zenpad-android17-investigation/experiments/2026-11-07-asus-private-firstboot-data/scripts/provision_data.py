"""Parent-only preparation of the actual sparse internal DATA image."""
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tarfile

ROOT = Path(__file__).resolve().parents[1]
PRIVATE = ROOT / 'private'
IMAGE = PRIVATE / 'firstboot-data.raw'
DEBUGFS = '/opt/homebrew/opt/e2fsprogs/sbin/debugfs'
E2FSCK = '/opt/homebrew/opt/e2fsprogs/sbin/e2fsck'
FACTORY = ROOT.parent / '2026-11-06-asus-factory-state-preservation/private'
SIZE = 11331268096
PRISTINE = '1602ea3644246871468b6987bc90e9a6e0c430f6b46efb4e79cc3555b688e0c1'


def exclusive(path, data):
    with path.open('xb') as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())


def db(command):
    p = subprocess.run([DEBUGFS, '-R', command, str(IMAGE)], capture_output=True,
                       text=True, timeout=20)
    if p.returncode:
        raise RuntimeError('debugfs failed')
    return p.stdout


def main():
    os.umask(0o077)
    correction = sys.argv[1:] == ['--finish-mode-correction']
    if sys.argv[1:] and not correction:
        raise RuntimeError('Unknown option')
    receipt = json.loads((PRIVATE / 'pristine-download.json').read_text())
    if receipt['sha256'] != PRISTINE or IMAGE.stat().st_size != SIZE or IMAGE.is_symlink():
        raise RuntimeError('Wrong downloaded DATA identity')
    if (PRIVATE / 'provision-started.json').exists() and not correction:
        raise RuntimeError('Preserve prior operation; no automatic rerun')
    if correction and ((PRIVATE / 'prepared-data-manifest.json').exists()
                       or "Couldn't parse '0o" not in (PRIVATE / 'debugfs.stderr').read_text()):
        raise RuntimeError('Not the observed debugfs octal syntax failure')
    if FACTORY.is_symlink() or FACTORY.stat().st_mode & 0o077:
        raise RuntimeError('Unsafe factory directory')
    records = json.loads((FACTORY / 'file-backup-verification.json').read_text())['sources']
    payloads = {}
    for name, expected_size in [('WIFI', 514), ('BT_Addr', 66)]:
        source = 'data/nvram/APCFG/APRDEB/' + name
        copies = []
        for suffix in ['a', 'b']:
            with tarfile.open(FACTORY / ('capture-' + suffix + '.tar'), 'r:') as archive:
                member = archive.getmember(source)
                if not (member.isfile() or member.islnk()):
                    raise RuntimeError('Unexpected source record type')
                with archive.extractfile(member) as stream:
                    data = stream.read(expected_size + 1)
                copies.append(data)
        if copies[0] != copies[1] or len(copies[0]) != expected_size:
            raise RuntimeError('Independent whole radio containers disagree')
        if hashlib.sha256(copies[0]).hexdigest() != records[source]['sha256']:
            raise RuntimeError('Preserved radio receipt mismatch')
        payloads[name] = copies[0]
    key = (Path.home() / '.android/adbkey.pub').read_bytes().strip()
    if b'\n' in key or b'\r' in key or len(base64.b64decode(key.split()[0], validate=True)) != 524:
        raise RuntimeError('Unexpected Android RSA public key format')
    payloads['adb_keys'] = key + b'\n'
    # These exact legacy files are natively imported by SDK37 init when its
    # aggregate persistent_properties file is absent. No hand-made protobuf.
    payloads['persist.adb.tcp.port'] = b'5555'
    payloads['persist.vendor.p00a.radio.enable'] = b'1'
    entries = [
        ('/misc', 'dir', 0o1771, 1000, 9998, 'system_data_file', None),
        ('/misc/adb', 'dir', 0o2750, 1000, 2000, 'adb_keys_file', None),
        ('/misc/adb/adb_keys', 'file', 0o640, 1000, 2000, 'adb_keys_file', 'adb_keys'),
        ('/property', 'dir', 0o700, 0, 0, 'property_data_file', None),
        ('/property/persist.adb.tcp.port', 'file', 0o600, 0, 0, 'property_data_file', 'persist.adb.tcp.port'),
        ('/property/persist.vendor.p00a.radio.enable', 'file', 0o600, 0, 0, 'property_data_file', 'persist.vendor.p00a.radio.enable'),
        ('/vendor', 'dir', 0o771, 0, 0, 'vendor_data_file', None),
        ('/vendor/p00a', 'dir', 0o751, 0, 0, 'p00a_radio_nvram_file', None),
        ('/vendor/p00a/nvram', 'dir', 0o751, 0, 0, 'p00a_radio_nvram_file', None),
        ('/vendor/p00a/nvram/APCFG', 'dir', 0o751, 0, 0, 'p00a_radio_nvram_file', None),
        ('/vendor/p00a/nvram/APCFG/APRDEB', 'dir', 0o751, 0, 0, 'p00a_radio_nvram_file', None),
        ('/vendor/p00a/nvram/APCFG/APRDEB/WIFI', 'file', 0o640, 0, 1010, 'p00a_radio_nvram_file', 'WIFI'),
        ('/vendor/p00a/nvram/APCFG/APRDEB/BT_Addr', 'file', 0o640, 0, 1002, 'p00a_radio_nvram_file', 'BT_Addr'),
    ]
    inputs = PRIVATE / 'inputs'
    inputs.mkdir(mode=0o700, exist_ok=correction)
    for name, data in payloads.items():
        if correction:
            if (inputs / name).read_bytes() != data:
                raise RuntimeError('Prepared input changed')
        else:
            exclusive(inputs / name, data)
    labels = {row[5] for row in entries}
    for label in labels:
        if not correction:
            exclusive(inputs / (label + '.label'), ('u:object_r:' + label + ':s0\0').encode())
    # A known empty pristine tree is the only accepted mutation baseline.
    listing = db('ls -p /')
    if not correction and any(name in listing for name in ['/misc/', '/vendor/', '/property/']):
        raise RuntimeError('Unexpected populated DATA tree')
    commands = []
    for path, kind, mode, uid, gid, label, name in entries:
        if not correction:
            commands.append('mkdir ' + path if kind == 'dir' else f'write {inputs / name} {path}')
        commands += [f'set_inode_field {path} mode 0{((0o40000 if kind == "dir" else 0o100000) | mode):o}',
                     f'set_inode_field {path} uid {uid}', f'set_inode_field {path} gid {gid}',
                     f'ea_set -f {inputs / (label + ".label")} {path} security.selinux']
    prefix = 'mode-correction' if correction else 'debugfs'
    batch = PRIVATE / (prefix + '.commands')
    exclusive(batch, ('\n'.join(commands) + '\n').encode())
    exclusive(PRIVATE / ('mode-correction-started.json' if correction else 'provision-started.json'), b'{"mutates_local_image_only":true}\n')
    p = subprocess.run([DEBUGFS, '-w', '-f', str(batch), str(IMAGE)],
                       capture_output=True, timeout=90)
    exclusive(PRIVATE / (prefix + '.stdout'), p.stdout)
    exclusive(PRIVATE / (prefix + '.stderr'), p.stderr)
    if p.returncode:
        raise RuntimeError('DATA modification failed; preserve partial image')
    for index, (path, kind, mode, uid, gid, label, name) in enumerate(entries):
        st = db('stat ' + path)
        if (not re.search(r'Mode:\s+0*' + format(mode, 'o') + r'\b', st)
                or not re.search(r'User:\s+' + str(uid) + r'\s+Group:\s+' + str(gid) + r'\b', st)):
            raise RuntimeError('Resulting inode ownership/mode mismatch: ' + path)
        attr = PRIVATE / ('label-readback-' + str(index))
        db(f'ea_get -f {attr} {path} security.selinux')
        if attr.read_bytes() != ('u:object_r:' + label + ':s0\0').encode():
            raise RuntimeError('Resulting SELinux label mismatch: ' + path)
        if kind == 'file':
            readback = PRIVATE / ('file-readback-' + str(index))
            db(f'dump {path} {readback}')
            if readback.read_bytes() != payloads[name]:
                raise RuntimeError('Resulting file bytes mismatch: ' + path)
    p = subprocess.run([E2FSCK, '-f', '-n', str(IMAGE)], capture_output=True, timeout=120)
    exclusive(PRIVATE / 'e2fsck.stdout', p.stdout)
    exclusive(PRIVATE / 'e2fsck.stderr', p.stderr)
    if p.returncode:
        raise RuntimeError('Read-only filesystem check failed')
    digest = hashlib.sha256()
    chunks = []
    with IMAGE.open('rb') as f:
        while chunk := f.read(1024 * 1024):
            digest.update(chunk)
            chunks.append(dict(bytes=len(chunk), sha256=hashlib.sha256(chunk).hexdigest(),
                               all_zero=chunk.count(0) == len(chunk)))
    result = dict(bytes=IMAGE.stat().st_size, sha256=digest.hexdigest(), chunk_bytes=1024*1024,
                  chunks=chunks, radio_containers_preserved=True, adb_public_key_only=True,
                  persistent_adb_port=5555, radio_opt_in=True, bluetooth_opt_in=False,
                  actual_file_readbacks=True, inode_and_selinux_checks=True, e2fsck_exit=0,
                  physical_operation_proven=False, device_writes=False, uploaded=False)
    exclusive(PRIVATE / 'prepared-data-manifest.json', (json.dumps(result, indent=2)+'\n').encode())
    print(json.dumps({k:v for k,v in result.items() if k != 'chunks'}))


if __name__ == '__main__':
    main()
