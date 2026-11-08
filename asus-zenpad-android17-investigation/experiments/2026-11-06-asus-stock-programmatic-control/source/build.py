#!/usr/bin/env python3
"""Offline local compilation only. Never launches the ARM64 ELF."""
import hashlib
import json
from pathlib import Path
import subprocess

S = Path(__file__).resolve().parents[1]
W = S.parent
CLANG = Path('/usr/bin/clang')
LLD = Path('/OWNER_HOME/.rustup/toolchains/1.97.1-aarch64-apple-darwin/lib/rustlib/aarch64-apple-darwin/bin/rust-lld')
LIB = W/'2026-11-06-asus-android17-os-rescue/artifacts/tools-final/libsepol'
OUT = S/'artifacts/build-v1'

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    OUT.mkdir(exist_ok=False)
    log=[]
    def run(args):
        p=subprocess.run(list(map(str,args)),capture_output=True,text=True,timeout=60)
        log.append(dict(argv=list(map(str,args)),returncode=p.returncode,stdout=p.stdout,stderr=p.stderr))
        if p.returncode: raise RuntimeError('Build failed; see evidence/build.json')
    try:
        run([CLANG,'--version']); run([LLD,'-flavor','gnu','--version'])
        run([CLANG,'--target=aarch64-linux-gnu','-Os','-ffreestanding','-fno-builtin',
             '-fno-stack-protector','-fno-pic','-fno-pie','-mgeneral-regs-only',
             '-Wall','-Wextra','-Werror','-c',S/'source/entry.c','-o',OUT/'entry.o'])
        run([LLD,'-flavor','gnu','-m','aarch64elf','-static','--build-id=none',
             '-e','_start','-o',OUT/'entry',OUT/'entry.o'])
        run([CLANG,'-O2','-Wall','-Wextra','-Werror','-I',LIB/'include',
             S/'source/policy_probe.c',LIB/'src/libsepol.a','-o',OUT/'policy_probe'])
    finally:
        (S/'evidence/build.json').write_text(json.dumps(dict(commands=log,sha256={
            str(p.relative_to(W)) if p.is_relative_to(W) else str(p):sha(p)
            for p in [CLANG,LLD,LIB/'src/libsepol.a',S/'source/entry.c',S/'source/policy_probe.c',
                      *OUT.iterdir()] if p.is_file()}),indent=2)+'\n')

if __name__=='__main__': main()
