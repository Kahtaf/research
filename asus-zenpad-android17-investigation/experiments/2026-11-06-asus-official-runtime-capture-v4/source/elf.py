"""Read ELF program headers and DT_NEEDED without executing target binaries."""
import struct
from safeio import need

def inspect(data):
    need(data[:4] == b'\x7fELF', 'ELF', 'missing ELF magic')
    cls, endian = data[4:6]
    need(cls in (1, 2) and endian == 1, 'ELF', 'only little-endian ELF32/64 supported')
    bits = 32 if cls == 1 else 64
    machine = struct.unpack_from('<H', data, 18)[0]
    need((bits, machine) in {(32, 40), (64, 183)}, 'ELF_ARCH', f'{bits}/{machine}')
    phoff = struct.unpack_from('<I' if cls == 1 else '<Q', data, 28 if cls == 1 else 32)[0]
    entsize, count = struct.unpack_from('<HH', data, 42 if cls == 1 else 54)
    need(entsize == (32 if cls == 1 else 56) and count <= 1024 and phoff + entsize * count <= len(data), 'ELF', 'program table bounds')
    loads, dynamic, interp = [], None, None
    for i in range(count):
        row = struct.unpack_from('<IIIIIIII' if cls == 1 else '<IIQQQQQQ', data, phoff + i * entsize)
        typ = row[0]
        off, va, size = (row[1], row[2], row[4]) if cls == 1 else (row[2], row[3], row[5])
        need(off + size <= len(data), 'ELF', 'segment bounds')
        if typ == 1:
            loads.append((va, off, size))
        if typ == 2:
            dynamic = (off, size)
        if typ == 3:
            interp = data[off:off+size].rstrip(b'\0').decode('ascii')
    names, table, table_size = [], None, None
    if dynamic:
        off, size = dynamic
        step = 8 if cls == 1 else 16
        need(size % step == 0, 'ELF', 'dynamic alignment')
        for pos in range(off, off + size, step):
            tag, value = struct.unpack_from('<iI' if cls == 1 else '<qQ', data, pos)
            if tag == 0:
                break
            if tag == 1:
                names.append(value)
            if tag == 5:
                table = value
            if tag == 10:
                table_size = value
    needed = []
    if names:
        need(table is not None and table_size is not None, 'ELF', 'missing string table')
        matches = [(o + table-v, table_size) for v,o,s in loads if v <= table and table + table_size <= v+s]
        need(len(matches) == 1, 'ELF', 'ambiguous string mapping')
        start, length = matches[0]
        for index in names:
            need(index < length, 'ELF', 'DT_NEEDED outside table')
            end = data.find(b'\0', start+index, start+length)
            need(end >= 0, 'ELF', 'unterminated DT_NEEDED')
            name = data[start+index:end].decode('ascii')
            need(name and '/' not in name and len(name) <= 256, 'ELF', 'unsafe DT_NEEDED')
            needed.append(name)
    return {'bits': bits, 'machine': machine, 'dt_needed': needed, 'interpreter': interp}
