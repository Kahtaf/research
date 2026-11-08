#!/usr/bin/env python3
"""Generate two UNSIGNED recovery candidates, offline, into a NEW directory.

No subprocess receives a device path. Inputs are bounded regular local files.
Private ADB keys are neither needed nor opened.
"""
import argparse
import base64
import gzip
import json
from pathlib import Path
import stat
import struct
import subprocess
from bootformat import (RECOVERY_SHA, KERNEL_SHA, PARTITION_SIZE, sha, parse_image,
                        ungzip, parse_cpio, make_cpio, wrap, make_image, elf_static)

SOURCE = Path(__file__).resolve().parent

def regular(path, limit):
    assert path.is_file() and stat.S_ISREG(path.stat().st_mode)
    assert path.stat().st_size <= limit
    return path.read_bytes()

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--recovery', type=Path, required=True)
    ap.add_argument('--recovery-verify', type=Path, required=True)
    ap.add_argument('--kernel', type=Path, required=True)
    ap.add_argument('--public-key', type=Path, required=True)
    ap.add_argument('--tools', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    assert not a.out.exists(), 'Refuse to overwrite any previous output'
    recovery = regular(a.recovery, PARTITION_SIZE)
    assert len(recovery) == PARTITION_SIZE and sha(recovery) == RECOVERY_SHA
    assert regular(a.recovery_verify, PARTITION_SIZE) == recovery
    kernel = regular(a.kernel, 16*1024*1024)
    assert sha(kernel) == KERNEL_SHA
    new_raw, dtb = ungzip(kernel)
    assert new_raw[56:60] == b'ARMd'
    assert sha(dtb) == '577a1ca5fbfe646ca02a50c190ac60efab0edd73c77c904a33865859e2d87bfc'
    h, k, r, trailer = parse_image(recovery)
    original_cmdline=h[64:576].split(b'\0')[0]
    assert original_cmdline.count(b'androidboot.selinux=permissive')==1
    cmdline=original_cmdline.replace(b'androidboot.selinux=permissive',b'androidboot.selinux=enforcing')
    assert len(cmdline)<512
    h=h[:64]+cmdline+bytes(512-len(cmdline))+h[576:]
    raw, extra = ungzip(r[512:]); assert not extra
    old = parse_cpio(raw)
    diag = regular(a.tools/'diag', 256*1024)
    for value in [diag, old['init'][3], old['sbin/adbd'][3]]: elf_static(value)
    # Only accept the public Android RSA format, strip identity comment.
    assert a.public_key.name.endswith('.pub'), 'Must explicitly supply a .pub public key'
    keytext = regular(a.public_key, 2048).decode('ascii').strip().split()[0]
    key = base64.b64decode(keytext, validate=True)
    assert len(key) == 524 and struct.unpack_from('<I', key)[0] == 64
    assert struct.unpack_from('<I', key, 520)[0] == 65537
    a.out.mkdir(parents=True, mode=0o700)
    stockpolicy = a.out/'stock-sepolicy'
    stockpolicy.write_bytes(old['sepolicy'][3])
    patched = a.out/'diagnostic-sepolicy'
    result = subprocess.run([str(a.tools/'policy_patch'), str(stockpolicy), str(patched)],
                            capture_output=True, text=True, check=True)
    (a.out/'policy-delta.txt').write_text(result.stdout)
    entries = {}
    for name in ['', 'dev', 'proc', 'sys', 'tmp', 'config', 'sbin', 'system', 'system/bin']:
        if name: entries[name]=(0o40755,0,0,b'')
    for name in ['init', 'sbin/adbd', 'file_contexts.bin', 'property_contexts',
                 'seapp_contexts', 'service_contexts']:
        entries[name]=old[name]
    entries['sbin/ueventd']=(0o120777,0,0,b'../init')
    entries['sbin/recovery']=(0o100750,0,0,diag)
    entries['system/bin/sh']=(0o100755,0,0,diag)
    entries['sepolicy']=(0o100644,0,0,patched.read_bytes())
    entries['adb_keys']=(0o100444,0,0,keytext.encode()+b'\n')
    for name in ['init.rc','default.prop','ueventd.rc']:
        entries[name]=(0o100644,0,0,(SOURCE/name).read_bytes())
    cpio = make_cpio(entries)
    assert parse_cpio(cpio) == entries
    # gzip mtime, OS byte and compression level fixed for deterministic output.
    gz = bytearray(gzip.compress(cpio,compresslevel=9,mtime=0)); gz[9]=255
    ramdisk = wrap(r, bytes(gz))
    images = {'UNTESTED-stock-control.img': make_image(h,k,ramdisk),
              'UNTESTED-asus49-probe.img': make_image(h,wrap(k,kernel),ramdisk)}
    for name,data in images.items():
        with (a.out/name).open('xb') as f: f.write(data)
    (a.out/'diagnostic.cpio.gz').write_bytes(gz)
    report = {
        'recovery_raw_sha256':RECOVERY_SHA, 'recovery_raw_bytes':len(recovery),
        'new_kernel_sha256':KERNEL_SHA, 'stock_kernel_wrapped_sha256':sha(k),
        'stock_recovery_roundtrip':True, 'partition_limit':PARTITION_SIZE,
        'original_header_cmdline':original_cmdline.decode(),
        'candidate_header_cmdline':cmdline.decode(),
        'load_addresses': {n:hex(struct.unpack_from('<I',h,o)[0]) for n,o in
                           [('kernel',12),('ramdisk',20),('tags',32)]},
        'stock_trailer_removed_bytes':len(trailer),
        'stock_trailer_removed_sha256':sha(trailer),
        'ramdisk_wrapped_sha256':sha(ramdisk),'ramdisk_cpio_bytes':len(cpio),
        'ramdisk_identical':True, 'public_key_rsa_sha256':sha(key),
        'public_key_comment_included':False, 'private_key_accessed':False,
        'static_elfs':{n:elf_static(entries[n][3]) for n in ['init','sbin/adbd','sbin/recovery','system/bin/sh']},
        'images':{n:{'bytes':len(b),'sha256':sha(b),'headroom':PARTITION_SIZE-len(b)} for n,b in images.items()},
        'entries':{n:{'mode':oct(m),'uid':u,'gid':g,'bytes':len(b),'sha256':sha(b)} for n,(m,u,g,b) in sorted(entries.items())},
        'sources':{p.name:sha(p.read_bytes()) for p in sorted(SOURCE.iterdir()) if p.is_file()},
        'tools':{n:sha((a.tools/n).read_bytes()) for n in ['diag','policy_patch','policy_query']},
        'asus_signature_valid':False,'hardware_validated':False,
        'ready_for_supervised_stock_control':False,
    }
    (a.out/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report['images'],indent=2))

if __name__ == '__main__': main()
