#!/usr/bin/env python3
"""Stage the bounded ASUS framebuffer graphics stack as real Soong prebuilts."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tarfile

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
EVIDENCE = ROOT / 'evidence/hardware-integration'
ROWS = json.loads((EVIDENCE / 'stock-elf-inventory.json').read_text())
CLOSURES = json.loads((EVIDENCE / 'framebuffer-graphics-closure.json').read_text())
INDEX = {row['path']: row for row in ROWS}
parser = argparse.ArgumentParser()
parser.add_argument('--revision', required=True)
args = parser.parse_args()
assert args.revision.isalnum()
STAGE = ROOT / ('artifacts/vendor-graphics-inputs-' + args.revision)
DEST = STAGE / 'vendor/asus/p00a'
assert not STAGE.exists(), 'Keep the existing staged inputs'
DEST.mkdir(parents=True)


def module(name):
    return 'p00a_legacy_' + name.removesuffix('.so').replace('.', '_').replace('-', '_').replace('+', 'x')


modules = {}
manifest = []
for closure in CLOSURES:
    bits = closure['bits']
    # Use Lineage's real legacy ION implementation and current libnetutils.
    # Duplicate stock copies otherwise collide with those platform modules.
    # The selected graphics stack imports no networking API from libnetutils.
    closure['libraries'].pop('libion.so', None)
    closure['libraries'].pop('libnetutils.so', None)
    # These pre-Treble blobs use the core ABI, including platform libstdc++.
    closure['libraries'].pop('libstdc++.so', None)
    for name, relative in closure['libraries'].items():
        row = INDEX[relative]
        source = WORKSPACE / relative
        assert hashlib.sha256(source.read_bytes()).hexdigest() == row['sha256']
        directory = 'lib64' if bits == 64 else 'lib'
        subdir = 'egl' if name == 'libGLES_mali.so' else 'hw' if name == 'gralloc.mt8163.so' else ''
        output = DEST / 'proprietary' / directory / subdir / name
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, output)
        dependencies = list(row['needed'])
        undefined = {symbol.split('@')[0] for symbol in row['undefined']}
        if any(symbol.startswith('__android_log_') for symbol in undefined):
            dependencies.append('liblog.so')
        if any(symbol.startswith(('sync_', 'sw_sync_')) for symbol in undefined):
            dependencies.append('libsync.so')
        if name in ('libGLES_mali.so', 'gralloc.mt8163.so'):
            dependencies.append('libutilscallstack.so')
        if name == 'gralloc.mt8163.so':
            dependencies.append('libp00a_legacy_memory.so')
        dependencies = list(dict.fromkeys(dependencies))
        shared = [module(dep) if dep in closure['libraries'] else
                  dep.removesuffix('.so') + ('#impl' if dep in
                  ('libc.so', 'libm.so', 'libdl.so', 'libsync.so') else '')
                  for dep in dependencies]
        modules.setdefault(name, {})[bits] = dict(src=str(output.relative_to(DEST)), shared=shared, subdir=subdir)
        manifest.append(dict(path=str(output.relative_to(DEST)), original_sha256=row['sha256'],
                             original_source=relative, original_needed=row['needed'],
                             additional_dependencies=[dep for dep in dependencies if dep not in row['needed']]))

parts = ['''// Generated for private ASUS Android 17 bring-up; firmware license unchanged.
package {
    default_applicable_licenses: ["p00a_vendor_graphics_license"],
}
license {
    name: "p00a_vendor_graphics_license",
    visibility: [":__subpackages__"],
    license_kinds: ["legacy_proprietary"],
}
''']
for name, variants in sorted(modules.items()):
    first = next(iter(variants.values()))
    multilib = 'both' if len(variants) == 2 else '64' if 64 in variants else '32'
    parts.append('cc_prebuilt_library_shared {\n' +
                 f'    name: "{module(name)}",\n' +
                 f'    stem: "{name.removesuffix(".so")}",\n' +
                 '    // Pre-Treble private core ABI; strict ELF validation remains enabled.\n' +
                 '    check_elf_files: true,\n' +
                 '    stl: "none",\n' +
                 '    system_shared_libs: [],\n' +
                 '    allow_undefined_symbols: false,\n' +
                 f'    compile_multilib: "{multilib}",\n' +
                 '    strip: { none: true },\n')
    if first['subdir']:
        parts.append(f'    relative_install_path: "{first["subdir"]}",\n')
    parts.append('    arch: {\n')
    for bits, variant in sorted(variants.items()):
        arch = 'arm64' if bits == 64 else 'arm'
        parts.append(f'        {arch}: {{\n            srcs: [{json.dumps(variant["src"])}],\n' +
                     '            shared_libs: ' + json.dumps(variant['shared']) + ',\n        },\n')
    parts.append('    },\n}\n')
symlinks = []
# EGL searches /vendor even on this pre-Treble device. Keep one core driver.
for bits in sorted(modules['libGLES_mali.so']):
    directory = 'lib64' if bits == 64 else 'lib'
    name = f'p00a_legacy_egl_path_{bits}'
    symlinks.append(name)
    parts.append('install_symlink {\n' + f'    name: "{name}",\n' +
                 '    vendor: true,\n' +
                 f'    installed_location: "{directory}/egl/libGLES_mali.so",\n' +
                 f'    symlink_target: "/system/{directory}/egl/libGLES_mali.so",\n' +
                 '    required: ["p00a_legacy_libGLES_mali"],\n}\n')
(DEST / 'Android.bp').write_text(''.join(parts))
(DEST / 'p00a-graphics-vendor.mk').write_text('# Generated ASUS framebuffer graphics modules.\nPRODUCT_PACKAGES += \\\n    ' + ' \\\n    '.join([module(name) for name in sorted(modules)] + symlinks) + '\n')
(DEST / 'input-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
with tarfile.open(ROOT / ('artifacts/vendor-graphics-inputs-' + args.revision + '.tar.gz'), 'w:gz') as archive:
    archive.add(STAGE / 'vendor', arcname='vendor')
print(f'Staged {len(modules)} modules / {len(manifest)} architecture-specific libraries')
print('Mali/gralloc copies require the saved dependency adaptation before compilation')
