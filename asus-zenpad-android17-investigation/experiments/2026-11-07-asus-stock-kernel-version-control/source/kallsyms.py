"""Stock kallsyms decoder retained from inspect_stock.py; no artifact reads/writes."""
import re, struct as S
align=lambda n,a:(n+a-1)//a*a
def decode(image):
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
    return symbols, sym, base, addresses
