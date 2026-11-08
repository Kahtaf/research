#!/usr/bin/env python3
"""Map the actual ASUS hardware libraries to dependencies needed by adapters."""
import hashlib
import json
from pathlib import Path
from elftools.elf.elffile import ELFFile

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
VENDOR = WORKSPACE / '2026-11-05-asus-latest-android-feasibility/evidence/device/vendor'
SYSTEM = ROOT / 'artifacts/stock-system-libraries'
OUTPUT = ROOT / 'evidence/hardware-integration'
CORE = {
    'libc.so', 'libdl.so', 'libm.so', 'liblog.so', 'libutils.so', 'libcutils.so',
    'libhardware.so', 'libhardware_legacy.so', 'libsync.so', 'libui.so', 'libgui.so',
    'libbinder.so', 'libnativewindow.so', 'libandroid.so', 'libandroid_runtime.so',
    'libEGL.so', 'libGLESv1_CM.so', 'libGLESv2.so', 'libGLESv3.so', 'libcrypto.so',
    'libssl.so', 'libz.so', 'libbase.so', 'libstdc++.so', 'libc++.so',
}


def read_elf(path):
    with path.open('rb') as stream:
        if stream.read(4) != b'\x7fELF':
            return None
        stream.seek(0)
        elf = ELFFile(stream)
        dynamic = elf.get_section_by_name('.dynamic')
        needed = []
        soname = path.name
        if dynamic:
            for tag in dynamic.iter_tags():
                if tag.entry.d_tag == 'DT_NEEDED':
                    needed.append(tag.needed)
                elif tag.entry.d_tag == 'DT_SONAME':
                    soname = tag.soname
        table = elf.get_section_by_name('.dynsym')
        undefined = []
        exports = []
        if table:
            for symbol in table.iter_symbols():
                if not symbol.name:
                    continue
                if symbol.entry.st_shndx == 'SHN_UNDEF':
                    if symbol.entry.st_info.bind != 'STB_WEAK':
                        undefined.append(symbol.name)
                elif symbol.entry.st_info.bind in ('STB_GLOBAL', 'STB_WEAK'):
                    exports.append(symbol.name)
        return dict(path=str(path.relative_to(WORKSPACE)), bits=elf.elfclass,
                    soname=soname, needed=needed, undefined=sorted(set(undefined)),
                    exports=sorted(set(exports)), bytes=path.stat().st_size,
                    sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def main():
    rows = []
    for folder in (VENDOR / 'lib', VENDOR / 'lib64', SYSTEM / 'lib', SYSTEM / 'lib64'):
        for path in sorted(folder.rglob('*')):
            if path.is_file():
                row = read_elf(path)
                if row:
                    row['source'] = 'vendor' if path.is_relative_to(VENDOR) else 'system'
                    rows.append(row)
    index = {(row['bits'], row['soname']): row for row in rows if row['source'] == 'system'}
    index.update({(row['bits'], row['soname']): row for row in rows if row['source'] == 'vendor'})
    platform_file = OUTPUT / 'platform-library-exports.json'
    platform = {(row['bits'], row['name']): row for row in
                json.loads(platform_file.read_text())['libraries']} if platform_file.exists() else {}
    roots = [row for row in rows if row['source'] == 'vendor' and
             (('/hw/' in row['path'] and row['soname'].startswith(
                 ('gralloc.', 'hwcomposer.', 'audio.primary.', 'sensors.'))) or
              row['soname'] == 'libGLES_mali.so')]
    reports = []
    for root in roots:
        seen = {}
        absent = set()
        stack = list(root['needed'])
        while stack:
            name = stack.pop()
            if name in seen or name in absent:
                continue
            dependency = index.get((root['bits'], name))
            if dependency is None:
                absent.add(name)
                continue
            seen[name] = dependency
            stack.extend(dependency['needed'])
        available = set().union(*(set(row['exports']) for row in [root, *seen.values()]))
        unresolved = sorted(set(root['undefined']) - available)
        modern_available = set(root['exports'])
        for name, row in seen.items():
            if name in CORE:
                modern_available.update(platform.get((root['bits'], name), {}).get('exports', []))
            else:
                modern_available.update(row['exports'])
        missing_after_core_replacement = {}
        unknown_core = {name for name in seen if name in CORE and (root['bits'], name) not in platform}
        for library in [root, *(row for name, row in seen.items() if name not in CORE)]:
            missing = set(library['undefined']) - modern_available
            confirmed = []
            unknown = []
            for symbol in sorted(missing):
                providers = [name for name, row in seen.items() if symbol in row['exports']]
                if set(providers) & unknown_core:
                    unknown.append(symbol)
                else:
                    confirmed.append(symbol)
            if confirmed or unknown:
                missing_after_core_replacement[library['soname']] = dict(
                    symbols_absent_from_built_android17_core=confirmed,
                    symbols_waiting_for_unbuilt_core_libraries=unknown)
        reports.append(dict(library=root['soname'], bits=root['bits'], direct=root['needed'],
                            transitive_count=len(seen), missing_libraries=sorted(absent),
                            unresolved_in_stock_closure=unresolved,
                            android17_abi_boundaries=sorted(CORE & seen.keys()),
                            unbuilt_android17_core=sorted(unknown_core),
                            symbol_adapters_needed=missing_after_core_replacement,
                            vendor_dependencies=sorted(name for name, row in seen.items() if row['source'] == 'vendor')))
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / 'stock-elf-inventory.json').write_text(json.dumps(rows, indent=2) + '\n')
    (OUTPUT / 'hardware-dependency-map.json').write_text(json.dumps(dict(
        scope='Real stock ELF dependencies; no Android 17 ABI/runtime compatibility claim',
        elf_count=len(rows), hardware_roots=reports), indent=2) + '\n')
    print(f'{len(rows)} real ELF files; {len(reports)} hardware entry points')
    for row in reports:
        print(f"{row['bits']} {row['library']}: {row['transitive_count']} dependencies, "
              f"{len(row['missing_libraries'])} missing libraries, "
              f"{len(row['unresolved_in_stock_closure'])} unresolved root symbols")
        confirmed = sum(len(item['symbols_absent_from_built_android17_core']) for item in row['symbol_adapters_needed'].values())
        print(f"  {confirmed} old symbol references absent from compiled Android 17 core; "
              f"{len(row['unbuilt_android17_core'])} core libraries not built yet")


if __name__ == '__main__':
    main()
