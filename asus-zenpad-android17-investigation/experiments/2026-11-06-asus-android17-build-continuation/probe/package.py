#!/usr/bin/env python3
"""Create a NEW, untested RAM-only 4.9 probe. No device access."""
import argparse,gzip,json,pathlib,struct,subprocess
from bootformat import *
from fdt import exact_initrd,parse
R=pathlib.Path(__file__).resolve().parents[1];OLD=R.parent/'2026-11-06-asus-android17-os-rescue'
def main():
    a=argparse.ArgumentParser();a.add_argument('--kernel',type=pathlib.Path,required=True);a.add_argument('--out',type=pathlib.Path,required=True);args=a.parse_args()
    control=(OLD/'artifacts/candidate-final/UNTESTED-stock-control.img').read_bytes()
    assert sha(control)=='7d74dfcaf4b2793453906799d721bfd95a401c564f6698b1c646e18bee918ea5'
    h,k,r,tail=parse_image(control);assert not tail
    assert struct.unpack_from('<I',h,12)[0]==0x40080000
    assert struct.unpack_from('<I',h,20)[0]==0x44000000
    assert struct.unpack_from('<I',h,24)[0]==0 and struct.unpack_from('<I',h,28)[0]==0x40f00000
    assert struct.unpack_from('<I',h,32)[0]==0x4e000000 and struct.unpack_from('<I',h,40)[0]==0
    old=parse_cpio(ungzip(r[512:])[0]);entries=dict(old)
    tools=R/'artifacts/probe-tools-r1';args.out.mkdir(parents=True,exist_ok=False)
    policy=args.out/'diagnostic-sepolicy'
    p=subprocess.run([str(tools/'policy_patch'),str(OLD/'artifacts/candidate-final/stock-sepolicy'),str(policy)],capture_output=True,check=True)
    (args.out/'policy-delta.txt').write_bytes(p.stdout)
    entries['config']=(0o40755,0,0,b'')
    for name in ['init.rc','default.prop','ueventd.rc']:entries[name]=(0o100644,0,0,(R/'probe'/name).read_bytes())
    for name in ['sbin/recovery','system/bin/sh']:entries[name]=(entries[name][0],0,0,(tools/'diag').read_bytes())
    entries['sepolicy']=(0o100644,0,0,policy.read_bytes())
    cpio=make_cpio(entries);assert parse_cpio(cpio)==entries
    gz=bytearray(gzip.compress(cpio,compresslevel=9,mtime=0));gz[9]=255;gz=bytes(gz)
    ramdisk=wrap(r,gz);payload=args.kernel.read_bytes();raw,dt=ungzip(payload);assert dt
    newdt=exact_initrd(dt,0x44000200,len(gz));compressed=payload[:-len(dt)]
    kernel=wrap(k,compressed+newdt)
    cmd=h[64:576].split(b'\0')[0];assert b'initrd=' not in cmd
    cmd+=f' initrd=0x44000200,0x{len(gz):x}'.encode();assert len(cmd)<512
    h=h[:64]+cmd+bytes(512-len(cmd))+h[576:]
    data=make_image(h,kernel,ramdisk);name='UNTESTED-combined-linux49-ram-probe.img'
    (args.out/name).write_bytes(data);(args.out/'diagnostic.cpio.gz').write_bytes(gz);(args.out/'packaged.dtb').write_bytes(newdt)
    report={'status':'UNTESTED; parent review and execution only','hardware_validated':False,'charging_permission_present':False,'input_kernel_sha256':sha(payload),'input_kernel_bytes':len(payload),'compressed_kernel_unchanged':True,'packaged_kernel_sha256':sha(kernel),'image_sha256':sha(data),'image_bytes':len(data),'padded_partition_sha256':sha(data+bytes(PARTITION_SIZE-len(data))),'partition_limit':PARTITION_SIZE,'ramdisk_compressed_bytes':len(gz),'ramdisk_payload_start':hex(0x44000200),'ramdisk_payload_end':hex(0x44000200+len(gz)),'header_cmdline':cmd.decode(),'dtb_sha256':sha(newdt),'policy_sha256':sha(policy.read_bytes()),'helper_sha256':sha((tools/'diag').read_bytes()),'entries':{n:{'mode':oct(m),'uid':u,'gid':g,'sha256':sha(v),'bytes':len(v)} for n,(m,u,g,v) in sorted(entries.items())}}
    assert not any('asus,allow-battery-charging' in props for props in parse(newdt)[1].values())
    (args.out/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='entries'},indent=2))
if __name__=='__main__':main()
