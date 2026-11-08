"""Verify two private independent factory archives without extracting payloads."""
from pathlib import Path
import datetime
import hashlib
import json
import re
import stat
import tarfile

ROOT = Path(__file__).resolve().parents[1]
PRIVATE = ROOT / 'private'
ROOTS = ('data/nvram', 'persist', 'data/misc/sensor', 'data/misc/akmd')


def inside(name):
    return not name.startswith('/') and '..' not in Path(name).parts and any(
        name == root or name.startswith(root + '/') for root in ROOTS)


def metadata(path):
    rows = {}
    for line in path.read_text().splitlines():
        fields = line.split('|', 8)
        if len(fields) != 9 or fields[-1] in rows or not inside(fields[-1]):
            raise ValueError('Malformed or duplicate source metadata')
        rows[fields[-1]] = dict(stat_mode=int(fields[0], 16), size=int(fields[1]),
                               uid=int(fields[2]), gid=int(fields[3]), mode=int(fields[4], 8),
                               mtime=int(fields[5]), ctime=int(fields[6]), inode=int(fields[7]))
    return rows


def verify_archive(path, observed):
    result = {}
    with tarfile.open(path, 'r:') as archive:
        for member in archive.getmembers():
            name = member.name.rstrip('/')
            if not inside(name) or name in result or name not in observed:
                raise ValueError('Unexpected, duplicate or unobserved archive path')
            source = observed[name]
            if (member.uid, member.gid, member.mode, int(member.mtime)) != (
                    source['uid'], source['gid'], source['mode'], source['mtime']):
                raise ValueError('Archive/source metadata mismatch')
            row = dict(type=member.type.decode(), mode=member.mode, uid=member.uid,
                       gid=member.gid, mtime=int(member.mtime))
            if member.isfile() or member.islnk():
                if not stat.S_ISREG(source['stat_mode']):
                    raise ValueError('Archive regular file/source type mismatch')
                if member.islnk() and not inside(member.linkname):
                    raise ValueError('External hardlink refused')
                stream = archive.extractfile(member)
                if stream is None:
                    raise ValueError('Missing archive data')
                data = stream.read()
                if len(data) != source['size']:
                    raise ValueError('Archive source size mismatch')
                row.update(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
            elif member.isdir():
                if not stat.S_ISDIR(source['stat_mode']):
                    raise ValueError('Directory/source type mismatch')
            elif member.issym():
                if not stat.S_ISLNK(source['stat_mode']):
                    raise ValueError('Symlink/source type mismatch')
                row['link_target'] = member.linkname
            elif member.isfifo() and name in {
                    'data/misc/sensor/fifo_cmd', 'data/misc/sensor/fifo_dat',
                    'data/misc/sensor/fifo_list'}:
                if not stat.S_ISFIFO(source['stat_mode']) or member.size != 0:
                    raise ValueError('FIFO/source type mismatch')
                # Preserve its metadata, never read IPC as calibration bytes.
                row['runtime_ipc_metadata_only'] = True
            else:
                raise ValueError('Unreviewed archive special file')
            result[name] = row
    if set(result) != set(observed):
        raise ValueError('Archive omitted observed entries')
    return result


def main():
    before = metadata(PRIVATE / 'stat-before.txt')
    after = metadata(PRIVATE / 'stat-after.txt')
    if before != after:
        raise ValueError('Source metadata changed during independent captures')
    a = verify_archive(PRIVATE / 'capture-a.tar', before)
    b = verify_archive(PRIVATE / 'capture-b.tar', before)
    if a != b:
        raise ValueError('Independent source captures differ')
    contexts = (PRIVATE / 'contexts.txt').read_text().splitlines()
    for name, row in a.items():
        matches = [line for line in contexts if line.endswith(' ' + name) or ' ' + name + ' -> ' in line]
        if len(matches) != 1:
            raise ValueError('Missing or ambiguous source SELinux metadata')
        label = re.findall(r'\bu:object_r:[A-Za-z0-9_]+:s0\b', matches[0])
        if len(label) != 1:
            raise ValueError('Unparsed source SELinux label')
        row['selinux_context'] = label[0]
    receipt = dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), sources=a,
                   source_stat=before, independent_source_captures_match=True,
                   source_metadata_stable=True, selinux_metadata_complete=True,
                   archive_a_sha256=hashlib.sha256((PRIVATE / 'capture-a.tar').read_bytes()).hexdigest(),
                   archive_b_sha256=hashlib.sha256((PRIVATE / 'capture-b.tar').read_bytes()).hexdigest())
    out = PRIVATE / 'file-backup-verification.json'
    if out.exists():
        raise ValueError('Preserve existing verification receipt')
    out.write_text(json.dumps(receipt, indent=2) + '\n')
    out.chmod(0o600)
    public = dict(utc=receipt['utc'], captured_entries=len(a),
                  regular_files_verified=sum('sha256' in row for row in a.values()),
                  runtime_fifo_metadata_only=sum(row.get('runtime_ipc_metadata_only', False) for row in a.values()),
                  source_metadata_stable=True, two_independent_captures_match=True,
                  selinux_metadata_complete=True, private_payloads_uploaded=False,
                  partition_writes=False, factory_preservation_complete=False)
    (ROOT / 'evidence/file-backup-status.json').write_text(json.dumps(public, indent=2) + '\n')
    print(json.dumps(public, indent=2))


if __name__ == '__main__':
    main()
