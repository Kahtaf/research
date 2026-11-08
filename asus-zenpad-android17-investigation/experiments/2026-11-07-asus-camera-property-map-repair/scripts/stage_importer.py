#!/usr/bin/env python3
"""Frozen ARM32 only: separate add-needed, then nine guarded equal-length writes.

No symbol rebuilding/reordering and no ELF execution. Run without Python -O.
"""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile
from integrity import (ADAPTER_SHA, MAPPING, NEEDED, ORIGINAL_SHA, PATCHELF_SHA,
                       Elf, compare, rename_plan, require, sha)


def rewrite(original, needed, adapter):
    require(sha(original.d) == ORIGINAL_SHA, 'wrong frozen original hash')
    require(sha(adapter.d) == ADAPTER_SHA, 'wrong existing ARM32 adapter hash')
    rename_plan(original)
    isolation = compare(original, needed, {})
    require(isolation['status'] == 'PASS', 'add-needed-only input fails integrity comparison')
    exports = {s[0] for s in adapter.syms if s[5] != 0 and s[3] >> 4 in (1, 2) and s[4] & 3 in (0, 3)}
    require(exports == set(MAPPING.values()), 'adapter must export exactly the nine private names')
    plan = rename_plan(needed)
    data = bytearray(needed.d)
    strings_offset = needed.sections['.dynstr'][4]
    writes = []
    for index, start, end, replacement in plan:
        offset = strings_offset + start
        data[offset:offset + len(replacement)] = replacement
        writes.append({'symbol_index': index, 'dynstr_start': start, 'dynstr_end_including_nul': end,
                       'file_offset': offset, 'old': needed.syms[index][0], 'new': replacement.decode()})
    candidate = Elf(bytes(data))
    result = compare(original, candidate, MAPPING)
    require(result['status'] == 'PASS', 'corrected candidate fails integrity comparison')
    require(candidate.body(candidate.sections['.dynsym']) == needed.body(needed.sections['.dynsym']), 'dynsym changed during rename')
    changed = [i for i, (a, b) in enumerate(zip(needed.d, data)) if a != b]
    allowed = {strings_offset + start + i for _, start, _, replacement in plan for i in range(len(replacement))}
    require(len(data) == len(needed.d) and set(changed) <= allowed, 'write outside eligible strings')
    result.update({'static_packaging_only': True, 'needed_only_sha256': sha(needed.d),
                   'adapter_sha256': sha(adapter.d), 'rename_changed_bytes': len(changed),
                   'rename_changed_file_offsets': changed, 'rename_writes': writes,
                   'rename_dynsym_bytes_unchanged': True, 'rename_hashed_suffix_unchanged': True,
                   'add_needed_isolation': isolation})
    return bytes(data), result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--original', type=Path, required=True)
    parser.add_argument('--adapter', type=Path, required=True)
    operation = parser.add_mutually_exclusive_group(required=True)
    operation.add_argument('--needed-only', type=Path, help='separately produced add-needed-only artifact; fully compared before use')
    operation.add_argument('--patchelf', type=Path, help='Linux pinned binary; invoked ONLY with --add-needed')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--receipt', type=Path, required=True)
    args = parser.parse_args()
    require(not args.output.exists() and not args.receipt.exists(), 'refusing to overwrite output or receipt')
    original, adapter = Elf(args.original), Elf(args.adapter)
    require(sha(original.d) == ORIGINAL_SHA, 'wrong frozen original hash')
    rename_plan(original)
    argv = None
    if args.needed_only:
        needed = Elf(args.needed_only)
    else:
        require(sha(args.patchelf.read_bytes()) == PATCHELF_SHA, 'wrong pinned patchelf hash')
        with tempfile.TemporaryDirectory(prefix='add-needed-', dir=args.output.parent) as directory:
            path = Path(directory) / 'needed-only.so'
            argv = [str(args.patchelf.resolve()), '--output', str(path), '--add-needed', NEEDED, str(args.original.resolve())]
            subprocess.run(argv, check=True, capture_output=True, timeout=20)
            needed = Elf(path)
    data, result = rewrite(original, needed, adapter)
    require(args.original.read_bytes() == original.d and args.adapter.read_bytes() == adapter.d, 'original input changed')
    result['local_add_needed_argv'] = argv
    with args.output.open('xb') as file:
        file.write(data)
    with args.receipt.open('x') as file:
        file.write(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in ('status', 'candidate_sha256', 'symbols', 'ordinary_relocations', 'aps2_relocations', 'relocation_mismatch_count', 'symbol_section_mismatch_count', 'rename_changed_bytes')}))


if __name__ == '__main__':
    main()
