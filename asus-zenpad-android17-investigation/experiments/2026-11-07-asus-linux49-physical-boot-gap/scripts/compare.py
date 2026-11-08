#!/usr/bin/env python3
"""Read only frozen public artifacts; emit small early-contract evidence."""
from pathlib import Path
import hashlib, json, struct, zlib

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT.parent
OUT = ROOT / 'evidence'
OUT.mkdir(exist_ok=True)
receipts = {}
def read(name):
    b = (WORK / name).read_bytes()
    receipts[name] = dict(bytes=len(b), sha256=hashlib.sha256(b).hexdigest())
    return b
def fdt(b):
    h = struct.unpack_from('>10I', b)
    assert h[0] == 0xd00dfeed and h[1] <= len(b)
    strings = b[h[3]:h[3]+h[8]]
    p, end, stack, nodes = h[2], h[2]+h[9], [], {}
    while p < end:
        t, = struct.unpack_from('>I', b, p); p += 4
        if t == 1:
            q = b.index(0, p); stack.append(b[p:q].decode()); p = (q+4)&~3
            nodes['/'.join(stack) or '/'] = {}
        elif t == 2: stack.pop()
        elif t == 3:
            n, off = struct.unpack_from('>II', b, p); p += 8
            name = strings[off:strings.index(0, off)].decode()
            nodes['/'.join(stack) or '/'][name] = b[p:p+n]; p = (p+n+3)&~3
        elif t == 9: break
        else: assert t == 4
    return b[:h[1]], nodes
STRINGS = {'model','compatible','device_type','enable-method','entry-method','method','status','clock-names','bootargs'}
def fmt(b, key):
    if not b: return True
    if key in STRINGS and b[-1:] == b'\0':
        return b.rstrip(b'\0').decode().split('\0')
    if len(b)%4 == 0: return ['0x%x' % x for x in struct.unpack('>%dI' % (len(b)//4), b)]
    return b.hex()
def inspect(label, payload):
    gz = zlib.decompressobj(31); image = gz.decompress(payload, 64*1024*1024)
    assert gz.eof
    dt, nodes = fdt(gz.unused_data)
    props = {}
    for path, ps in nodes.items():
        comp = ps.get('compatible', b'').lower()
        if path in ('/','/chosen') or path.startswith(('/cpus','/memory','/psci','/reserved-memory')) or any(x in comp for x in (b'timer',b'gic',b'clk',b'clock',b'mt8163',b'sysirq',b'infracfg',b'topckgen',b'apmixed',b'mcucfg')):
            props[path] = {k:fmt(v,k) for k,v in ps.items()}
    raw = dict(image_bytes=len(image), image_sha256=hashlib.sha256(image).hexdigest(),
               gzip_bytes=len(payload)-len(gz.unused_data), dt_bytes=len(dt), dt_sha256=hashlib.sha256(dt).hexdigest(),
               image_header=dict(text_offset=hex(struct.unpack_from('<Q',image,8)[0]), image_size=hex(struct.unpack_from('<Q',image,16)[0]),flags=hex(struct.unpack_from('<Q',image,24)[0])), nodes=props)
    (OUT / (label+'-contract.json')).write_text(json.dumps(raw,indent=2)+'\n')
    # Preserve only config text, never a duplicated Image.
    marker = image.find(b'IKCFG_ST')
    if marker >= 0:
        cfg = zlib.decompressobj(31).decompress(image[marker+8:])
        (OUT / (label+'-embedded.config')).write_bytes(cfg)
        raw['embedded_config_sha256'] = hashlib.sha256(cfg).hexdigest()
    print(label, json.dumps({k:v for k,v in raw.items() if k != 'nodes'}))
    for path,ps in props.items():
        if path=='/' or path.startswith(('/cpus','/memory','/psci')) or any(x in str(ps.get('compatible','')) for x in ('timer','gic','sysirq')):
            print(path, json.dumps(ps))
    return image, nodes

stock=read('2026-11-05-asus-boot-access-audit/artifacts/device-backup/initial/recovery.bin')
assert receipts[next(iter(receipts))]['sha256']=='902b2f06a01cca574b4aa374e67c4e7f8f0ed53f6e6a55017b6d96351f0f1f20'
ks,=struct.unpack_from('<I',stock,8); page,=struct.unpack_from('<I',stock,36)
assert hashlib.sha256(stock[page:page+ks]).hexdigest()=='b0e5d48bf2889b418dda0fc867f70e42e27a0aeb0a0a3d37539d9a7435430880'
stock_payload=stock[page+512:page+ks]
assert stock[page+512:].rfind(b'\xd0\x0d\xfe\xed',1,ks+4)==7409347
inspect('stock',stock_payload)
e9=read('2026-11-06-asus-bmc156-full-kernel/artifacts/Image.gz-dtb')
assert hashlib.sha256(e9).hexdigest()=='e9cde06e85e752aec0433ea37fa926c31b4f7a72cd55453762ec6870e5bb5bf1'
inspect('e9',e9)
r2=read('2026-11-07-asus-linux49-usb-ram-report-r2/artifacts/candidate.img')
assert hashlib.sha256(r2).hexdigest()=='291b824fca69544253ea55ad91e1edf95d0d651dd8c5400c999a8d946c3dc915'
ks,=struct.unpack_from('<I',r2,8); page,=struct.unpack_from('<I',r2,36)
assert r2[page+512:].rfind(b'\xd0\x0d\xfe\xed',1,ks+4)==7653276
r2image,r2nodes=inspect('r2',r2[page+512:page+ks])
assert r2nodes['/chosen']['linux,initrd-start']==bytes.fromhex('44000000')
assert r2nodes['/chosen']['linux,initrd-end']==bytes.fromhex('4403e4a3')
assert b'initrd=' not in r2[64:576]
print('r2-header-cmdline',r2[64:576].split(b'\0')[0].decode())
cfg=read('2026-11-06-asus-bmc156-full-kernel/artifacts/resolved.config')
assert cfg==(OUT/'e9-embedded.config').read_bytes()
(OUT/'input-receipts.json').write_text(json.dumps(receipts,indent=2)+'\n')
