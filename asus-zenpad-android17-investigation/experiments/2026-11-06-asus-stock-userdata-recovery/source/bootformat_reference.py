"""Read-only bounded gzip/newc helpers adapted from os-rescue bootformat.py."""
import zlib
def align(n, unit=2048):
    return (n + unit - 1) // unit * unit


def ungzip(data, limit=64*1024*1024):
    d = zlib.decompressobj(31)
    raw = d.decompress(data, limit+1)
    assert len(raw) <= limit and d.eof and not d.unconsumed_tail
    return raw, d.unused_data

def parse_cpio(data):
    entries, pos = {}, 0
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
        assert name not in entries
        entries[name] = (f[1], f[2], f[3], value)

