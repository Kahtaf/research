"""Bounded offline readers/writers for this unit's Android v0 + MTK format."""
import hashlib
import struct
import zlib

RECOVERY_SHA = '902b2f06a01cca574b4aa374e67c4e7f8f0ed53f6e6a55017b6d96351f0f1f20'
KERNEL_SHA = '7c7051c147b03ca865b3481d55cd832bc6f2732eef1c0063af9404823b0ceaa4'
PARTITION_SIZE = 16740352

def sha(data):
    return hashlib.sha256(data).hexdigest()

def align(n, unit=2048):
    return (n + unit - 1) // unit * unit

def pad(data, unit=2048):
    return data + bytes(align(len(data), unit) - len(data))

def boot_id(kernel, ramdisk):
    return hashlib.sha1(kernel + struct.pack('<I', len(kernel)) + ramdisk +
                        struct.pack('<II', len(ramdisk), 0)).digest() + bytes(12)

def parse_image(data):
    assert len(data) <= PARTITION_SIZE and data[:8] == b'ANDROID!'
    ks, ka, rs, ra, ss, sa, ta, page = struct.unpack_from('<8I', data, 8)
    assert page == 2048 and ss == 0
    ro = page + align(ks)
    end = ro + align(rs)
    assert end <= len(data)
    kernel, ramdisk = data[page:page+ks], data[ro:ro+rs]
    assert data[576:608] == boot_id(kernel, ramdisk)
    for value, name in [(kernel, b'KERNEL'), (ramdisk, b'RECOVERY')]:
        assert value[:4] == bytes.fromhex('88168858')
        assert struct.unpack_from('<I', value, 4)[0] == len(value)-512
        assert value[8:40].split(b'\0')[0] == name
    assert data == data[:page] + pad(kernel) + pad(ramdisk) + data[end:]
    return data[:page], kernel, ramdisk, data[end:]

def ungzip(data, limit=64*1024*1024):
    d = zlib.decompressobj(31)
    raw = d.decompress(data, limit+1)
    assert len(raw) <= limit and d.eof and not d.unconsumed_tail
    return raw, d.unused_data

def parse_cpio(data):
    entries, pos = {}, 0
    repeated_directories = set()
    while True:
        h = data[pos:pos+110]
        assert h[:6] == b'070701' and len(h) == 110
        f = [int(h[6+8*i:14+8*i], 16) for i in range(13)]
        size, ns = f[6], f[11]
        assert 0 < ns < 4096 and size <= 16*1024*1024
        namebytes = data[pos+110:pos+110+ns]
        assert namebytes[-1:] == b'\0'
        name = namebytes[:-1].decode()
        pos = align(pos+110+ns, 4)
        value = data[pos:pos+size]
        assert len(value) == size
        pos = align(pos+size, 4)
        if name == 'TRAILER!!!':
            assert not any(data[pos:])
            return entries
        assert name and not name.startswith('/') and '..' not in name.split('/')
        if name in entries:
            assert name == 'dev' and f[1] == 0o040755 and f[2:4] == [0, 0]
            assert size == 0 and entries[name] == (f[1], f[2], f[3], value)
            assert name not in repeated_directories
            repeated_directories.add(name)
            continue
        entries[name] = (f[1], f[2], f[3], value)

def make_cpio(entries):
    out = bytearray()
    for ino, (name, (mode, uid, gid, value)) in enumerate(
            list(sorted(entries.items())) + [('TRAILER!!!', (0, 0, 0, b''))], 1):
        n = name.encode() + b'\0'
        fields = [ino, mode, uid, gid, 2 if mode & 0o170000 == 0o040000 else 1,
                  0, len(value), 0, 0, 0, 0, len(n), 0]
        out += b'070701' + ''.join(f'{v:08x}' for v in fields).encode() + n
        out = bytearray(pad(out, 4)); out += value; out = bytearray(pad(out, 4))
    return pad(out, 512)

def wrap(template, payload):
    h = bytearray(template[:512])
    struct.pack_into('<I', h, 4, len(payload))
    return bytes(h) + payload

def make_image(header, kernel, ramdisk):
    h = bytearray(header)
    struct.pack_into('<I', h, 8, len(kernel))
    struct.pack_into('<I', h, 16, len(ramdisk))
    h[576:608] = boot_id(kernel, ramdisk)
    result = bytes(h) + pad(kernel) + pad(ramdisk)
    assert len(result) <= PARTITION_SIZE
    return result

def elf_static(data):
    assert data[:6] == b'\x7fELF\x02\x01'
    assert struct.unpack_from('<H', data, 18)[0] == 183
    off = struct.unpack_from('<Q', data, 32)[0]
    size, count = struct.unpack_from('<HH', data, 54)
    types = [struct.unpack_from('<I', data, off+i*size)[0] for i in range(count)]
    assert 2 not in types and 3 not in types, 'Dynamic/interpreter dependency'
    return {'elf_class': 64, 'machine': 'AArch64', 'static': True}
