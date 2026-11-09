"""Report ELF64 PT_TLS segments and DT_NEEDED for files given as arguments (read-only)."""
import struct
import sys

PT_TLS, PT_DYNAMIC, DT_NEEDED, DT_STRTAB = 7, 2, 1, 5

for path in sys.argv[1:]:
    with open(path, "rb") as fh:
        data = fh.read()
    if data[:4] != b"\x7fELF" or data[4] != 2:
        continue
    phoff = struct.unpack_from("<Q", data, 0x20)[0]
    phentsize, phnum = struct.unpack_from("<HH", data, 0x36)
    tls = None
    loads = []
    dyn = None
    for i in range(phnum):
        p_type, _flags, p_offset, p_vaddr, _pa, p_filesz, p_memsz, _al = struct.unpack_from(
            "<IIQQQQQQ", data, phoff + i * phentsize)
        if p_type == PT_TLS:
            tls = (p_filesz, p_memsz)
        if p_type == 1:
            loads.append((p_vaddr, p_offset, p_filesz))
        if p_type == PT_DYNAMIC:
            dyn = (p_offset, p_filesz)

    def v2o(vaddr):
        for va, off, sz in loads:
            if va <= vaddr < va + sz:
                return vaddr - va + off
        return None

    needed, strtab = [], None
    if dyn:
        off, sz = dyn
        for j in range(0, sz, 16):
            tag, val = struct.unpack_from("<qQ", data, off + j)
            if tag == 0:
                break
            if tag == DT_NEEDED:
                needed.append(val)
            if tag == DT_STRTAB:
                strtab = v2o(val)
    names = []
    if strtab is not None:
        for n in needed:
            end = data.index(b"\0", strtab + n)
            names.append(data[strtab + n:end].decode())
    label = f"PT_TLS filesz={tls[0]} memsz={tls[1]}" if tls else "no-TLS"
    print(f"{path.split('/x/', 1)[-1]}\t{label}\tNEEDED={','.join(names)}")
