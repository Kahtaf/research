#!/usr/bin/env python3
"""Read an official downloaded boot.img; unpack MTK gzip payloads without executing them."""
import gzip, hashlib, json, re, struct, zlib
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
source = ROOT / 'sources/stock-firmware/boot.img'
out = source.parent / 'unpacked'
out.mkdir(exist_ok=True)
b = source.read_bytes()
assert b[:8] == b'ANDROID!'
k, ka, r, ra, s, sa, tags, page = struct.unpack_from('<8I', b, 8)
def aligned(n): return (n + page - 1) // page * page
result = dict(sha256=hashlib.sha256(b).hexdigest(), image_bytes=len(b), kernel_bytes=k, ramdisk_bytes=r, page_bytes=page, cmdline=b[64:576].split(b'\0')[0].decode())
for name, start, size in [('kernel', page, k), ('ramdisk', page+aligned(k), r)]:
    raw = b[start:start+size]
    (out / (name+'-mtk.bin')).write_bytes(raw)
    skip = 512 if raw[:4] == bytes.fromhex('88168858') else 0
    obj = zlib.decompressobj(16+zlib.MAX_WBITS)
    data = obj.decompress(raw[skip:]) + obj.flush()
    (out / ('Image' if name == 'kernel' else 'ramdisk.cpio')).write_bytes(data)
    result[name] = dict(wrapper_bytes=skip, uncompressed_bytes=len(data), trailing_bytes=len(obj.unused_data))
    if name == 'kernel':
        m = re.search(rb'Linux version [^\0\n]+', data)
        result['linux_version'] = m.group().decode(errors='replace') if m else None
        configstart = data.find(b'IKCFG_ST')
        result['embedded_config_found'] = configstart >= 0
        if configstart >= 0:
            configend = data.index(b'IKCFG_ED', configstart)
            (out/'kernel.config').write_bytes(gzip.decompress(data[configstart+8:configend]))
        trailing = obj.unused_data
        dtbs = []
        while trailing:
            magic = trailing.find(bytes.fromhex('d00dfeed'))
            if magic < 0: break
            n = struct.unpack_from('>I', trailing, magic+4)[0]
            assert 40 <= n <= len(trailing)-magic
            p = out / ('appended-%d.dtb' % len(dtbs))
            p.write_bytes(trailing[magic:magic+n])
            dtbs.append(dict(file=p.name, bytes=n))
            trailing = trailing[magic+n:]
        result['appended_dtbs'] = dtbs
(ROOT/'evidence/stock-boot-unpack.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps(result, indent=2))
