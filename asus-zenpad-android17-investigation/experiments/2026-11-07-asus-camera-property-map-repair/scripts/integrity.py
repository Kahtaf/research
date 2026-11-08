"""Static checks for the frozen ARM32 shape, including APS2 from elf32.py."""
import hashlib
import struct
from collections import Counter
from elf32 import Elf

ORIGINAL_SHA = 'be8cb386e5f5ea7045b24017870d85b67774518f6e9ae9efd3ed1c00f5dcdcec'
BAD_SHA = '625bfeb69cdc3118661588264e030d2ec07be96e9f3cf967a66f79eba0e743fa'
ADAPTER_SHA = 'd371807e43c770306100670d2cd2dad1e6a00262b1f2483f266cbd72ecef4405'
PATCHELF_SHA = '35fc95654387035338a74bb8cf62fde3712ec83dd8ca30a768deb714d07f063a'
NEEDED = 'libasus_camera_legacy_property_map.so'
NAMES = (
    '_ZN7android11PropertyMap11addPropertyERKNS_7String8ES3_',
    '_ZN7android11PropertyMap5clearEv',
    '_ZN7android11PropertyMapC1Ev',
    '_ZN7android11PropertyMapD1Ev',
    '_ZNK7android11PropertyMap11hasPropertyERKNS_7String8E',
    '_ZNK7android11PropertyMap14tryGetPropertyERKNS_7String8ERS1_',
    '_ZNK7android11PropertyMap14tryGetPropertyERKNS_7String8ERb',
    '_ZNK7android11PropertyMap14tryGetPropertyERKNS_7String8ERf',
    '_ZNK7android11PropertyMap14tryGetPropertyERKNS_7String8ERi',
)
MAPPING = {n: n.replace('11PropertyMap', '11AsusPropMap') for n in NAMES}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def raw_symbols(e):
    b = e.body(e.sections['.dynsym'])
    return [struct.unpack_from('<IIIBBH', b, i) for i in range(0, len(b), 16)]


def string_references(e):
    """Every consumer of this input's .dynstr, including version auxiliary names."""
    refs = [('symbol:%d' % i, x[0]) for i, x in enumerate(raw_symbols(e))]
    allowed = {'.dynsym', '.dynamic', '.gnu.version_r', '.gnu.version_d'}
    dynstr_index = e.names.index('.dynstr')
    for name, h in e.sections.items():
        if h[6] == dynstr_index:
            require(name in allowed, 'unexpected .dynstr consumer: ' + name)
    for i, (tag, value) in enumerate(e.dyn):
        if tag in (1, 14, 15, 29, 0x7ffffffd, 0x7fffffff):
            refs.append(('dynamic:%d' % i, value))
    b = e.body(e.sections['.gnu.version_r'])
    pos = 0
    for i in range(e.tags[0x6fffffff]):
        require(pos + 16 <= len(b), 'version need out of bounds')
        version, count, file, aux, nxt = struct.unpack_from('<HHIII', b, pos)
        require(version == 1 and count > 0, 'unexpected version need')
        refs.append(('verneed:%d' % i, file))
        ap = pos + aux
        for j in range(count):
            require(ap + 16 <= len(b), 'version need aux out of bounds')
            _, _, _, name, an = struct.unpack_from('<IHHII', b, ap)
            refs.append(('vernaux:%d:%d' % (i, j), name))
            require((j + 1 == count) == (an == 0), 'version need aux chain')
            ap += an
        require((i + 1 == e.tags[0x6fffffff]) == (nxt == 0), 'version need chain')
        pos += nxt
    b = e.body(e.sections['.gnu.version_d'])
    pos = 0
    for i in range(e.tags[0x6ffffffd]):
        require(pos + 20 <= len(b), 'version def out of bounds')
        version, _, _, count, _, aux, nxt = struct.unpack_from('<HHHHIII', b, pos)
        require(version == 1 and count > 0, 'unexpected version def')
        ap = pos + aux
        for j in range(count):
            require(ap + 8 <= len(b), 'version def aux out of bounds')
            name, an = struct.unpack_from('<II', b, ap)
            refs.append(('verdaux:%d:%d' % (i, j), name))
            require((j + 1 == count) == (an == 0), 'version def aux chain')
            ap += an
        require((i + 1 == e.tags[0x6ffffffd]) == (nxt == 0), 'version def chain')
        pos += nxt
    for label, offset in refs:
        require(0 <= offset < len(e.strings), label + ': string offset out of bounds')
        e.z(e.strings, offset)
    return refs


def layout(e):
    require(__debug__, 'run without Python -O')
    require(len(e.syms) == 419, 'unexpected symbol count')
    require(e.sections['.dynsym'][9] == 16 and e.tags[11] == 16, 'symbol entry size')
    require(e.tags[10] == len(e.strings), 'DT_STRSZ')
    require(e.tags[19] == 8 and e.tags[20] == 17, 'expected ARM32 REL')
    require(e.tags[2] == e.sections['.rel.plt'][5], 'DT_PLTRELSZ')
    require(e.tags[0x60000010] == e.sections['.rel.dyn'][5], 'DT_ANDROID_RELSZ')
    require(e.sections['.rel.dyn'][1] == 0x60000001, 'expected APS2 REL section')
    for tag, length, section in [(3, 4, '.got'), (25, e.tags[27], '.init_array'), (26, e.tags[28], '.fini_array')]:
        h = e.sections[section]
        require(h[3] <= e.tags[tag] and e.tags[tag] + length <= h[3] + h[5], 'dynamic pointer: ' + section)
    for name, target in [('.gnu.hash', '.dynsym'), ('.gnu.version', '.dynsym'), ('.rel.plt', '.dynsym'), ('.dynamic', '.dynstr'), ('.gnu.version_r', '.dynstr'), ('.gnu.version_d', '.dynstr')]:
        require(e.sections[name][6] == e.names.index(target), 'section link: ' + name)
    require(e.sections['.rel.plt'][7] == e.names.index('.plt'), 'PLT section target')
    require(len(e.body(e.sections['.gnu.version'])) == 2 * len(e.syms), 'version count')
    nb, first, nw, shift = struct.unpack_from('<4I', e.body(e.sections['.gnu.hash']))
    require((nb, first, nw, shift) == (263, 142, 64, 11), 'unexpected GNU-hash scope')
    require(all(s[5] != 0 for s in e.syms[first:]), 'undefined import inside hashed suffix')
    require('.hash' not in e.sections, 'unexpected second hash table')
    refs = string_references(e)
    return {'dynamic_string_references': len(refs), 'gnu_hash_first_symbol': first,
            'gnu_hash_lookups': e.hashcheck(), 'load_mappings_valid': True,
            'dynamic_pointers_valid': True, 'version_string_references_valid': True}


def rename_plan(e):
    checks = layout(e)
    require([s[0] for s in e.syms if 'PropertyMap' in s[0]] == list(NAMES), 'wrong original names/count/order')
    require(not any('AsusPropMap' in s[0] for s in e.syms), 'private names already present')
    refs = string_references(e)
    raw = raw_symbols(e)
    versions = e.body(e.sections['.gnu.version'])
    plan = []
    for old, new in MAPPING.items():
        indices = [i for i, s in enumerate(e.syms) if s[0] == old]
        require(len(indices) == 1, 'duplicate/missing original import')
        i = indices[0]
        offset, value, size, info, other, section = raw[i]
        require((value, size, info, other, section) == (0, 0, 0x12, 0, 0), 'import definition/binding/visibility mismatch')
        require(struct.unpack_from('<H', versions, i * 2)[0] == 0, 'versioned target import')
        require(i < checks['gnu_hash_first_symbol'], 'target import in GNU hash')
        a, b = old.encode(), new.encode()
        end = offset + len(a) + 1
        require(a != b and len(a) == len(b), 'rename must be distinct and equal length')
        require(offset > 0 and end <= len(e.strings), 'rename range out of bounds')
        require(e.strings[offset - 1] == 0 and e.strings[offset:end] == a + b'\0', 'target is not a complete string')
        require(all(end <= start or offset >= stop for _, start, stop, _ in plan), 'overlapping rename ranges')
        for label, start in refs:
            stop = e.strings.index(0, start) + 1
            if start < end and offset < stop:
                require(label == 'symbol:%d' % i and start == offset, 'reused/conflicting rename range: ' + label)
        plan.append((i, offset, end, b))
    return plan


def addend(e, address):
    matches = [p for p in e.ph if p[0] == 1 and p[2] <= address and address + 4 <= p[2] + p[5]]
    require(len(matches) == 1, 'relocation target LOAD mapping')
    p = matches[0]
    off = address - p[2]
    require(off + 4 <= p[4] or off >= p[4], 'partial zero-fill addend')
    return struct.unpack_from('<I', e.d, p[1] + off)[0] if off < p[4] else 0


def compare(old, new, mapping):
    old_layout, new_layout = layout(old), layout(new)
    expected = [(mapping.get(s[0], s[0]), *s[1:]) for s in old.syms]
    byname = {s[0]: s for s in new.syms}
    require(len(byname) == len(new.syms), 'duplicate dynamic symbol name')
    section_errors = [dict(name=s[0], old_section=s[5], new_section=byname.get(mapping.get(s[0], s[0]), ('',)*6)[5])
                      for s in old.syms if s[5] != byname.get(mapping.get(s[0], s[0]), ('',)*6)[5]]
    ordered_errors = sum(a != b for a, b in zip(expected, new.syms))
    reloc_errors = []
    counts = Counter()
    intended = []
    def records(e, rename):
        out = []
        for address, info in e.rel():
            index, typ = info >> 8, info & 255
            require(index < len(e.syms), 'relocation symbol index out of bounds')
            s = e.syms[index]
            out.append((address, typ, addend(e, address), rename.get(s[0], s[0]), *s[1:]))
        return sorted(out)
    ra, rb = records(old, mapping), records(new, {})
    require(len(ra) == len(rb), 'relocation count changed')
    section_reloc_errors = 0
    for a, b in zip(ra, rb):
        counts[str(a[1])] += 1
        if a[:8] != b[:8]:
            reloc_errors.append({'expected': a, 'actual': b})
        section_reloc_errors += a != b
        if a[3] in mapping.values():
            intended.append({'address': hex(a[0]), 'type': a[1], 'addend': hex(a[2]), 'name': a[3]})
    if mapping:
        require(len(intended) == 9 and {x['name'] for x in intended} == set(mapping.values()), 'expected nine import relocations')
    versions_equal = all(old.body(old.sections[n]) == new.body(new.sections[n]) for n in ('.gnu.version', '.gnu.version_r', '.gnu.version_d'))
    expected_needed = [NEEDED] + old.needed
    dependencies_equal = new.needed == expected_needed
    # Metadata may move; every other allocated section must retain its address and bytes.
    allowed = {'.interp', '.note.android.ident', '.note.gnu.build-id', '.dynsym', '.dynstr', '.dynamic'}
    allocated_errors = [n for n, h in old.sections.items() if h[2] & 2 and n not in allowed and
                        (h[3] != new.sections[n][3] or old.body(h) != new.body(new.sections[n]))]
    # Original st_name, value, size, info and visibility stay at the same indices.
    raw_fields_equal = all(a[:5] == b[:5] for a, b in zip(raw_symbols(old), raw_symbols(new)))
    # All original string bytes survive except the explicit nine renames; add-needed only appends.
    strings = bytearray(old.strings)
    for i, s in enumerate(old.syms):
        if s[0] in mapping:
            offset = raw_symbols(old)[i][0]
            strings[offset:offset + len(s[0])] = mapping[s[0]].encode()
    strings_equal = new.strings[:len(strings)] == strings
    passed = not (reloc_errors or section_errors or ordered_errors or allocated_errors) and all((versions_equal, dependencies_equal, raw_fields_equal, strings_equal))
    return {'status': 'PASS' if passed else 'FAIL', 'original_sha256': sha(old.d), 'candidate_sha256': sha(new.d),
            'symbols': len(old.syms), 'relocations': len(ra), 'ordinary_relocations': len(old.body(old.sections['.rel.plt'])) // 8,
            'aps2_relocations': len(ra) - len(old.body(old.sections['.rel.plt'])) // 8,
            'relocation_types': dict(counts), 'relocation_mismatch_count': len(reloc_errors), 'relocation_mismatches': reloc_errors,
            'relocation_mismatches_including_section_metadata': section_reloc_errors,
            'symbol_section_mismatch_count': len(section_errors), 'symbol_section_mismatches': section_errors,
            'ordered_symbol_mismatch_count': ordered_errors, 'raw_symbol_fields_except_section_index_equal': raw_fields_equal,
            'version_bytes_equal': versions_equal, 'ordered_dependencies_equal': dependencies_equal, 'needed': new.needed,
            'original_dynstr_prefix_except_renames_equal': strings_equal, 'unexpected_allocated_section_changes': allocated_errors,
            'intended_import_relocations': intended, 'original_layout': old_layout, 'candidate_layout': new_layout,
            'runtime_executed': False}
