#!/usr/bin/env python3
"""Create deliberately NONBOOTABLE v0 fixtures from real kernel/probe bytes."""
import gzip, json, struct
from pathlib import Path
from bootformat import sha, boot_id, pad, parse_image, ungzip, parse_cpio, make_cpio
from lk_contract import REQUIRED_INPUT
from package_full_boot import package
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT.parent/'2026-11-06-asus-android17-build-continuation'
PINS={'Image.gz-dtb-combined-r1':'d4094bcff6c763af7f1c01ccd3d612a988f96de13f78b492b808cc76c0ac929f', 'Image.gz-dtb-combined-product-r3':'84007607154fd2b7d5f69dff63a1474589d2b6ddd0086511ff1cca4f34ebd59f'}


def fixture(kernel, ram):
    h=bytearray(2048);h[:8]=b'ANDROID!'
    struct.pack_into('<10I',h,8,len(kernel),0x40080000,len(ram),0x44000000,0,0x40f00000,0x4e000000,2048,0,0)
    h[48:64]=b'NONBOOTABLE'+bytes(5)
    cmd=b' '.join(k+b'='+v for k,v in REQUIRED_INPUT.items())
    h[64:64+len(cmd)]=cmd;h[576:608]=boot_id(kernel,ram)
    return bytes(h)+pad(kernel)+pad(ram)


def inputs():
    probe_path=ROOT.parent/'2026-11-06-asus-linux49-probe-initrd-fix/artifacts/probe-r3/UNTESTED-combined-linux49-ram-probe-r3.img'
    probe=probe_path.read_bytes()
    assert sha(probe)=='45551fec6af489bef6813131fb3854eddcfe95d3ca3fa640fea7a37dfd21b630'
    _,pk,pr,_=parse_image(probe)
    entries=parse_cpio(ungzip(pr[512:])[0]);init=entries['init'][3]
    # Real compiled probe /init retained as non-executable reference DATA, not /init.
    cpio=make_cpio({'NONBOOTABLE-SYNTHETIC-FIXTURE.txt':(0o100644,0,0,b'PACKAGING TEST ONLY. No init; never install or flash.\n'),
                    'fixture-reference-init.bin':(0o100644,0,0,init),
                    'fstab.mt8163':(0o100644,0,0,(ROOT/'source/aosp/device/asus/p00a/rootdir/fstab.mt8163').read_bytes())})
    return gzip.compress(cpio,mtime=0),pr[512:]


def main():
    ram,real_probe_ram=inputs();receipts={}
    for name,expected in PINS.items():
        kernel=(BASE/'artifacts'/name).read_bytes();assert sha(kernel)==expected
        data=fixture(kernel,ram);report={'boot':{'sha256':sha(data)},'synthetic':True}
        image,dt,result=package(data,kernel,report,synthetic=True)
        out=ROOT/'artifacts'/name;out.mkdir(parents=True,exist_ok=True)
        (out/'NONBOOTABLE-SYNTHETIC-AOSP-input.img').write_bytes(data)
        (out/'input-report.json').write_text(json.dumps(report,indent=2)+'\n')
        (out/'NONBOOTABLE-SYNTHETIC-full-BOOT.img').write_bytes(image)
        (out/'packaged.dtb').write_bytes(dt)
        (out/'manifest.json').write_text(json.dumps(result,indent=2)+'\n')
        receipts[name]=result
    (ROOT/'evidence/fixture-results.json').write_text(json.dumps(receipts,indent=2)+'\n')
    print(json.dumps({name:{k:r[k] for k in ('image_bytes','image_sha256','header_cmdline_bytes','ramdisk_bytes')} for name,r in receipts.items()},indent=2))

if __name__=='__main__':main()
