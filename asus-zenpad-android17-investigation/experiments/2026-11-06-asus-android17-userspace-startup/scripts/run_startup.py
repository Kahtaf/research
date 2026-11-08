#!/usr/bin/env python3
"""Run compiled Android 17 userspace against the existing virtual 4.9 kernel."""
from pathlib import Path
import argparse
import gzip
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess

ROOT = Path('/srv/android/asus-userspace-startup')
TREE = Path('/srv/android/lineage24')
PRODUCT = TREE / 'out/target/product/p00a'
parser = argparse.ArgumentParser()
parser.add_argument('--kernel', default='/srv/android/asus-userspace-startup/kernel-build/arch/arm64/boot/Image')
parser.add_argument('--run-name', default='run-r2-advice')
args = parser.parse_args()
assert '/' not in args.run_name and args.run_name not in ('', '.', '..')
KERNEL = Path(args.kernel)
OUT = ROOT / args.run_name
assert not OUT.exists(), 'Preserve the first run and use a new run directory for a changed fixture'
OUT.mkdir()
clang = TREE / 'prebuilts/clang/host/linux-x86/clang-r584948b/bin/clang'
resource = Path(subprocess.check_output([str(clang), '-print-resource-dir'], text=True).strip())
crt = TREE / 'out/soong/.intermediates/bionic/libc'
command = [str(clang), '--target=aarch64-linux-android37', '-O2', '-Wall', '-Werror',
           '-nostdinc', '-nostdlib', '-fPIE', '-pie', '-Wl,--dynamic-linker=/system/bin/linker64']
for include in [TREE / 'bionic/libc/include', TREE / 'bionic/libc/kernel/uapi/asm-arm64',
                TREE / 'bionic/libc/kernel/uapi', TREE / 'bionic/libc/kernel/android/uapi', resource / 'include']:
    command += ['-isystem', str(include)]
command += [str(crt / 'crtbegin_dynamic/android_arm64_armv8-a/crtbegin_dynamic.o'),
            str(ROOT / 'sources/libc_smoke.c'),
            '-L' + str(PRODUCT / 'system/lib64/bootstrap'), '-lc', '-ldl', '-lm',
            str(crt / 'crtend_android/android_arm64_armv8-a/crtend_android.o'), '-o', str(OUT / 'libc-smoke')]
subprocess.run(command, check=True)
subprocess.run(['aarch64-linux-gnu-gcc', '-static', '-O2', '-Wall', '-Werror',
                str(ROOT / 'sources/guest_init.c'), '-o', str(OUT / 'init')], check=True)

files = {'init': (OUT / 'init').read_bytes(),
         'system/bin/toybox': (PRODUCT / 'system/bin/toybox').read_bytes(),
         'system/bin/linker64': (PRODUCT / 'system/bin/bootstrap/linker64').read_bytes(),
         'system/bin/libc-smoke': (OUT / 'libc-smoke').read_bytes(),
         'entropy.seed': os.urandom(64)}
libraries = {}
pending = [PRODUCT / 'system/bin/toybox', OUT / 'libc-smoke']
directories = [PRODUCT / 'system/lib64/bootstrap', PRODUCT / 'system/lib64', PRODUCT / 'system_ext/lib64']
while pending:
    path = pending.pop()
    dynamic = subprocess.check_output(['readelf', '-d', str(path)], text=True)
    for name in re.findall(r'Shared library: \[(.*?)\]', dynamic):
        if name == 'ld-android.so' or name in libraries:
            continue
        library = next((directory / name for directory in directories if (directory / name).is_file()), None)
        assert library, f'Missing compiled dependency {name} of {path}'
        libraries[name] = library
        pending.append(library)
for name, path in libraries.items():
    files['system/lib64/' + name] = path.read_bytes()

archive = bytearray()
def entry(name, mode, contents=b'', major=0, minor=0):
    encoded = name.encode() + b'\0'
    fields = [1, mode, 0, 0, 1, 0, len(contents), 0, 0, major, minor, len(encoded), 0]
    archive.extend(b'070701' + ''.join(f'{value:08x}' for value in fields).encode())
    archive.extend(encoded)
    archive.extend(b'\0' * (-len(archive) % 4))
    archive.extend(contents)
    archive.extend(b'\0' * (-len(archive) % 4))

folders = {'dev', 'proc', 'sys', 'tmp', 'linkerconfig'}
for name in files:
    folders.update(str(parent) for parent in Path(name).parents if str(parent) != '.')
for name in sorted(folders, key=lambda name: (name.count('/'), name)):
    entry(name, stat.S_IFDIR | 0o755)
for name, major, minor in [('dev/console', 5, 1), ('dev/null', 1, 3), ('dev/random', 1, 8), ('dev/urandom', 1, 9)]:
    entry(name, stat.S_IFCHR | 0o600, major=major, minor=minor)
for name, data in sorted(files.items()):
    entry(name, stat.S_IFREG | (0o755 if name == 'init' or '/bin/' in name else 0o400 if name == 'entropy.seed' else 0o644), data)
entry('TRAILER!!!', 0)
initramfs = OUT / 'initramfs.cpio.gz'
initramfs.write_bytes(gzip.compress(archive, mtime=0))
manifest = [dict(path=name, bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
            for name, data in files.items() if name != 'entropy.seed']
(OUT / 'input-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
qemu = ['qemu-system-aarch64', '-machine', 'virt,gic-version=3', '-cpu', 'cortex-a53',
        '-smp', '2', '-m', '1024', '-nographic', '-monitor', 'none', '-no-reboot', '-nic', 'none',
        '-kernel', str(KERNEL), '-initrd', str(initramfs),
        '-append', 'console=ttyAMA0 earlycon=pl011,0x9000000 rdinit=/init panic=-1 loglevel=6']
log = OUT / 'qemu.log'
timed_out = False
with log.open('w') as stream:
    try:
        result = subprocess.run(qemu, stdin=subprocess.DEVNULL, stdout=stream, stderr=subprocess.STDOUT, timeout=120)
        code = result.returncode
    except subprocess.TimeoutExpired:
        timed_out = True
        code = None
text = log.read_text(errors='replace')
match = re.search(r'ANDROID17_STARTUP_RESULT (\{[^\r\n]+\})', text)
report = dict(scope='Actual SDK 37 userspace on generic ARM64 Linux 4.9; no Android framework/ASUS hardware boot',
              qemu_returncode=code, timed_out=timed_out, result=json.loads(match[1]) if match else None,
              passed='ANDROID17_STARTUP_PASSED' in text and 'ANDROID17_LIBC_FORK_OK' in text and code == 0,
              kernel_sha256=hashlib.sha256(KERNEL.read_bytes()).hexdigest(),
              qemu_command=qemu, android_libc_sha256=hashlib.sha256(files['system/lib64/libc.so']).hexdigest())
(OUT / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
assert report['passed'], 'Read the actual guest log before changing the fixture or compatibility code'
