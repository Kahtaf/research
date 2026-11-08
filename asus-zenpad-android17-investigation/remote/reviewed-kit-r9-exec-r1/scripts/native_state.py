"""Read selected Siso v1.5.8 metadata without invoking the native engine."""
import gzip
import hashlib
import io
from pathlib import Path
import struct


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for data in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(data)
    return h.hexdigest()


def varint(stream):
    value = shift = 0
    while True:
        data = stream.read(1)
        if not data:
            if shift:
                raise ValueError('Truncated native-state varint')
            return None
        value |= (data[0] & 127) << shift
        if data[0] < 128:
            return value
        shift += 7
        if shift >= 70:
            raise ValueError('Invalid native-state varint')


def fields(data):
    stream = io.BytesIO(data)
    result = {}
    while (tag := varint(stream)) is not None:
        number, wire = tag >> 3, tag & 7
        if wire == 0:
            value = varint(stream)
        elif wire == 2:
            size = varint(stream)
            if size is None or size > 1024 * 1024:
                raise ValueError('Oversized native-state field')
            value = stream.read(size)
            if len(value) != size:
                raise ValueError('Truncated native-state field')
        elif wire in (1, 5):
            value = stream.read(8 if wire == 1 else 4)
        else:
            raise ValueError('Unsupported native-state wire type')
        result[number] = value
    return result


def digest(data):
    if data is None:
        return None
    row = fields(data)
    return {'hash': row.get(1, b'').decode(), 'size_bytes': row.get(2, 0)}


def selected_state(aosp, targets):
    aosp = Path(aosp)
    aliases = {str(aosp / target): target for target in targets}
    aliases.update({target: target for target in targets})
    path = aosp / 'out/.siso_fs_state'
    before = path.stat()
    result = {}
    with gzip.open(path, 'rb') as stream:
        while (tag := varint(stream)) is not None:
            size = varint(stream)
            if tag & 7 != 2 or size is None or size > 1024 * 1024:
                raise ValueError('Unsupported native-state message')
            data = stream.read(size)
            if len(data) != size:
                raise ValueError('Truncated native-state message')
            if tag >> 3 != 1:
                continue
            row = fields(data)
            name = row.get(2, b'').decode()
            target = aliases.get(name)
            if target is None:
                continue
            result[target] = {
                'name': name,
                'mtime_ns': fields(row[1]).get(1),
                'digest': digest(row.get(3)),
                'cmd_hash_hex': row.get(6, b'').hex(),
                'edge_hash_hex': row.get(9, b'').hex(),
                'action': digest(row.get(7)),
                'updated_time_ns': row.get(8, 0),
                'local': bool(row.get(10, 0)),
                'target': row.get(5, b'').decode(),
            }
    after = path.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise ValueError('Native state changed during selected read')
    return result


def selected_deps(aosp, targets):
    """Current Ninja-deps v4 paths/mtime; never historical input-byte proof."""
    path = Path(aosp) / 'out/.siso_deps'
    before = path.stat()
    aliases = {target: target for target in targets}
    aliases.update({str(Path(aosp) / target): target for target in targets})
    ids, records = {}, {}

    def scan():
        with path.open('rb') as stream:
            if stream.read(16) != b'# ninjadeps\n' + struct.pack('<I', 4):
                raise ValueError('Unsupported native dependency store')
            index = 0
            while raw := stream.read(4):
                if len(raw) != 4:
                    raise ValueError('Truncated native dependency header')
                value = struct.unpack('<I', raw)[0]
                size = value & 0x7fffffff
                if size < 4 or size % 4 or size > 4 * 1024 * 1024:
                    raise ValueError('Invalid native dependency record')
                data = stream.read(size)
                if len(data) != size:
                    raise ValueError('Truncated native dependency record')
                if value >> 31:
                    yield True, struct.unpack_from('<I', data)[0], data
                else:
                    if struct.unpack_from('<I', data, size - 4)[0] != (~index & 0xffffffff):
                        raise ValueError('Native dependency node identity changed')
                    yield False, index, data[:-4].rstrip(b'\0')
                    index += 1

    for is_deps, index, data in scan():
        if not is_deps:
            name = data.decode()
            if name in aliases:
                ids[index] = aliases[name]
        elif index in ids:
            values = struct.unpack('<' + 'I' * (len(data) // 4), data)
            records[ids[index]] = {'mtime_ns': values[1] | values[2] << 32,
                                   'ids': list(values[3:])}
    wanted = {value for row in records.values() for value in row['ids']}
    names = {}
    for is_deps, index, data in scan():
        if not is_deps and index in wanted:
            names[index] = data.decode()
    for row in records.values():
        row['dependencies'] = [names[index] for index in row.pop('ids')]
    after = path.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise ValueError('Native dependencies changed during selected read')
    return records


def artifact(path):
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError('Native output must be a regular file: ' + str(path))
    st = path.stat()
    result = {'sha256': sha(path), 'bytes': st.st_size, 'mtime_ns': st.st_mtime_ns}
    with path.open('rb') as stream:
        header = stream.read(64)
        if len(header) == 64 and header[:6] == b'\x7fELF\x02\x01':
            result['elf_machine'] = struct.unpack_from('<H', header, 18)[0]
            phoff = struct.unpack_from('<Q', header, 32)[0]
            phsize, count = struct.unpack_from('<HH', header, 54)
            ids = []
            if count > 1024:
                raise ValueError('Oversized ELF program-header table')
            for number in range(count):
                stream.seek(phoff + number * phsize)
                ph = stream.read(phsize)
                if len(ph) < 56 or struct.unpack_from('<I', ph)[0] != 4:
                    continue
                offset, length = struct.unpack_from('<Q', ph, 8)[0], struct.unpack_from('<Q', ph, 32)[0]
                if length > 1024 * 1024:
                    raise ValueError('Oversized ELF note')
                stream.seek(offset)
                data = stream.read(length)
                pos = 0
                while pos + 12 <= len(data):
                    ns, ds, kind = struct.unpack_from('<III', data, pos)
                    pos += 12
                    name = data[pos:pos + ns].rstrip(b'\0'); pos += (ns + 3) & ~3
                    value = data[pos:pos + ds]; pos += (ds + 3) & ~3
                    if name == b'GNU' and kind == 3:
                        ids.append(value.hex())
            result['build_ids'] = ids
    return result
