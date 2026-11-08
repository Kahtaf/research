from pathlib import Path
import hashlib, json, re, struct as S, zlib
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
R=Path(__file__).resolve().parents[1]
W=R.parent
rec=(W/'2026-11-05-asus-boot-access-audit/artifacts/device-backup/initial/recovery.bin').read_bytes()
assert hashlib.sha256(rec).hexdigest()=='902b2f06a01cca574b4aa374e67c4e7f8f0ed53f6e6a55017b6d96351f0f1f20'
image=zlib.decompress(rec[2560:],31)
assert hashlib.sha256(image).hexdigest()=='db90ee7fff379f35ac2b0aafb11a6abee7b2c283b57d352c40ae7c6d7c35eb2a'
align=lambda n,a:(n+a-1)//a*a
# Decode and cross-check every exact stock symbol, preserving only selected slices.
b = image; runs = []; start = None
for i in range(0, len(b)-7, 8):
    v = S.unpack_from('<Q', b, i)[0]
    if v >> 32 == 0xffffffc0:
        if start is None: start = i
    else:
        if start is not None and i-start > 400000: runs.append((start, i))
        start = None
assert len(runs) == 1
a, e = runs[0]; n = (e-a)//8; num = align(e, 256)
assert S.unpack_from('<Q', b, num)[0] == n == 70337
addresses = S.unpack_from('<'+'Q'*n, b, a); assert list(addresses) == sorted(addresses)
names = align(num+8, 256); p = names; encoded = []; markers = []
for i in range(n):
    if i % 256 == 0: markers.append(p-names)
    size = b[p]; assert 0 < size < 128
    encoded.append(b[p+1:p+1+size]); p += size+1
mo = align(p, 256); assert list(S.unpack_from('<'+'Q'*len(markers), b, mo)) == markers
to = align(mo+8*len(markers), 256); p = to; tokens = []; idx = []
for _ in range(256):
    idx.append(p-to); end = b.index(0, p); tokens.append(b[p:end].decode()); p = end+1
io = align(p, 256); assert list(S.unpack_from('<256H', b, io)) == idx
symbols = []
for addr, enc in zip(addresses, encoded):
    text = ''.join(tokens[t] for t in enc); assert re.fullmatch(r'[a-zA-Z?][a-zA-Z0-9_.$@]+', text)
    symbols.append((addr, text[1:]))
sym = {name: addr for addr, name in symbols}; base = sym.get('_text', 0xffffffc000080000)
rev = {addr: name for addr, name in symbols}

md=Cs(CS_ARCH_ARM64,CS_MODE_ARM); lines=[]; facts={}
for addr,name in symbols:
 if not any(x in name for x in ['wdt','wd_api','wk_kthread','wk_start','get_boot_reason','set_boot_reason','boot_reason_init','arch_reset']): continue
 off=addr-base; size=min(v for v in addresses if v>addr)-addr
 facts[name]={'address':hex(addr),'image_offset':off,'bytes':size,'sha256':hashlib.sha256(b[off:off+size]).hexdigest()}
 if name.endswith('_file_ops'): continue
 lines.append('FUNCTION %s %#x bytes=%d'%(name,addr,size))
 for ins in md.disasm(b[off:off+size],addr):
  note=''
  if ins.mnemonic in ('bl','b') and ins.op_str.startswith('#'): note=' ; '+rev.get(int(ins.op_str[1:],16),'?')
  lines.append('%016x %s %s %s%s'%(ins.address,ins.bytes.hex(),ins.mnemonic,ins.op_str,note))
 lines.append('')
(R/'evidence/stock-watchdog.disasm').write_text('\n'.join(lines)+'\n')
(R/'evidence/stock-watchdog-symbols.json').write_text(json.dumps(facts,indent=2)+'\n')
print(json.dumps(facts,indent=2))
