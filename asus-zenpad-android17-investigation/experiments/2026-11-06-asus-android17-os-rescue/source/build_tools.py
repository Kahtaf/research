#!/usr/bin/env python3
"""Local-only bounded builds. Writes only a new directory supplied by caller."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile

SOURCE = Path(__file__).resolve().parent

def run(cmd, log):
    p = subprocess.run([str(x) for x in cmd], capture_output=True, text=True)
    log.append({'argv': [str(x) for x in cmd], 'returncode': p.returncode,
                'stdout': p.stdout, 'stderr': p.stderr})
    if p.returncode:
        raise RuntimeError(p.stderr or p.stdout)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--clang', default=shutil.which('clang'))
    ap.add_argument('--lld', required=True, help='ELF-capable ld.lld or rust-lld')
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=False)
    log = []
    try:
        archive = SOURCE/'libsepol-android-7.1.2_r39.tar.gz'
        assert hashlib.sha256(archive.read_bytes()).hexdigest() == 'c17c444d73f1080a8959cfda2d4bdb529efd88f5af58a9e571917f473f83ff27'
        lib = a.out/'libsepol'
        with tarfile.open(archive) as t:
            assert sum(m.size for m in t.getmembers()) < 10*1024*1024
            t.extractall(lib, filter='data')
        flags = '-O2 -Wno-error'
        if os.uname().sysname == 'Darwin': flags += ' -DDARWIN -D_DARWIN_C_SOURCE'
        run(['make', '-C', lib/'src', 'libsepol.a', 'DISABLE_CIL=y',
             f'CC={a.clang}', f'CFLAGS={flags}', '-j4'], log)
        for name in ['policy_query', 'policy_patch', 'policy_constraints']:
            run([a.clang, '-O2', '-I', lib/'include', SOURCE/f'{name}.c',
                 lib/'src/libsepol.a', '-o', a.out/name], log)
        run([a.clang, '--target=aarch64-linux-gnu', '-Os', '-ffreestanding',
             '-fno-builtin', '-fno-stack-protector', '-fno-pic', '-fno-pie',
             '-mgeneral-regs-only', '-Wall', '-Wextra', '-Werror', '-c',
             SOURCE/'diag.c', '-o', a.out/'diag.o'], log)
        run([a.lld, '-flavor', 'gnu', '-m', 'aarch64elf', '-static',
             '--build-id=none', '-e', '_start', '-o', a.out/'diag', a.out/'diag.o'], log)
        run([a.clang, '-O1', '-Wall', '-Wextra', '-Werror', '-fsanitize=address,undefined',
             SOURCE/'test_diag.c', '-o', a.out/'test_diag'], log)
        run([a.out/'test_diag'], log)
        run([a.clang, '--version'], log)
        run([a.lld, '-flavor', 'gnu', '--version'], log)
    finally:
        (a.out/'build.json').write_text(json.dumps(log, indent=2)+'\n')

if __name__ == '__main__': main()
