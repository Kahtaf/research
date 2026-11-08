#!/usr/bin/env python3
"""Package a successful AOSP BOOT with exact MTK geometry and ramdisk bounds."""
import pathlib,sys,argparse,struct,json,hashlib
R=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'probe'))
from bootformat import sha,pad,wrap,boot_id,ungzip,PARTITION_SIZE
from fdt import parse,exact_initrd
from boot_memory import check_memory
p=argparse.ArgumentParser();p.add_argument('--aosp-boot',type=pathlib.Path,required=True);p.add_argument('--build-report',type=pathlib.Path,required=True);p.add_argument('--kernel',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args()
b=a.aosp_boot.read_bytes();m=json.loads(a.build_report.read_text());assert sha(b)==m['boot']['sha256']
assert b[:8]==b'ANDROID!';ks,ka,rs,ra,ss,sa,ta,page=struct.unpack_from('<8I',b,8)
assert (ka,ra,ss,ta,page)==(0x40080000,0x44000000,0,0x4e000000,2048);assert sa in (0,0x40f00000);assert struct.unpack_from('<I',b,40)[0]==0
ro=page+(ks+page-1)//page*page;k=b[page:page+ks];ram=b[ro:ro+rs]
assert b[576:608]==boot_id(k,ram);assert k==a.kernel.read_bytes();assert not ungzip(ram)[1]
assert not any(b[608:1632]),'Extended cmdline needs explicit supported merge'
cmd=b[64:576].split(b'\0')[0];assert not any(t.startswith(b'initrd=') for t in cmd.split())
for arg in [b'androidboot.hardware=mt8163',b'androidboot.fstab_suffix=mt8163',b'androidboot.boot_devices=soc/11230000.mmc']:assert arg in cmd.split()
assert b'androidboot.selinux=permissive' not in cmd
if b'androidboot.selinux=enforcing' not in cmd.split():cmd+=b' androidboot.selinux=enforcing'
raw,dt=ungzip(k);newdt=exact_initrd(dt,0x44000200,len(ram),cmd)
memory=check_memory(raw,newdt,len(ram))
assert not any('asus,allow-battery-charging' in props for props in parse(newdt)[1].values())
provenance=json.loads((R/'evidence/stock-wrapper-provenance.json').read_text());kw=(R/'inputs/stock-kernel-wrapper.bin').read_bytes();rw=(R/'inputs/stock-ramdisk-wrapper.bin').read_bytes()
assert sha(kw)==provenance['kernel_wrapper_sha256'] and sha(rw)==provenance['ramdisk_wrapper_sha256']
wk=wrap(kw,k[:-len(dt)]+newdt);wr=wrap(rw,ram)
cmd+=f' initrd=0x44000200,0x{len(ram):x}'.encode();assert len(cmd)<512
h=bytearray(b[:page]);struct.pack_into('<I',h,8,len(wk));struct.pack_into('<I',h,16,len(wr));struct.pack_into('<I',h,28,0x40f00000);h[64:576]=cmd+bytes(512-len(cmd));h[576:608]=boot_id(wk,wr)
image=bytes(h)+pad(wk)+pad(wr);assert len(image)<=PARTITION_SIZE and 0x44000200+len(ram)<0x4e000000
assert ungzip(wr[512:])[0]==ungzip(ram)[0]
a.out.mkdir(parents=True,exist_ok=False);(a.out/'UNTESTED-sdk37-combined-boot.img').write_bytes(image);(a.out/'packaged.dtb').write_bytes(newdt)
report={'aosp_boot_sha256':sha(b),'input_kernel_sha256':sha(k),'image_sha256':sha(image),'image_bytes':len(image),'padded_partition_sha256':sha(image+bytes(PARTITION_SIZE-len(image))),'partition_bytes':PARTITION_SIZE,'compressed_kernel_unchanged':True,'ramdisk_compressed_unchanged':True,'ramdisk_start':hex(0x44000200),'ramdisk_end':hex(0x44000200+len(ram)),'ramdisk_bytes':len(ram),'header_cmdline':cmd.decode(),'dtb_sha256':sha(newdt),'memory_layout':memory,'hardware_boot_validated':False,'asus_signature_valid':False,'wrapper_provenance':provenance}
(a.out/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
