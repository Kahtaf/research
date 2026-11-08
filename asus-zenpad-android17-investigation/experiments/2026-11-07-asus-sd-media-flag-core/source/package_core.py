"""Pinned Linux4.9/MTK package; only chosen metadata changes for RAM size."""
import gzip,struct
import bootformat as b
from fdt import parse
from lk_contract import HEADER,chosen_dt,kernel_config,model_lk_gzip
from boot_memory import check_memory
KERNEL_SHA='e9cde06e85e752aec0433ea37fa926c31b4f7a72cd55453762ec6870e5bb5bf1'
CONFIG_SHA='10b212cabd28aad012582e86c64695ccd450650b4e09ec8da30c21e094f377c2'
def package(entries,compiled,header,kw,rw):
 if len(compiled)!=7716897 or b.sha(compiled)!=KERNEL_SHA:raise ValueError('exact existing physical kernel required')
 raw,dt=b.ungzip(compiled);assert dt
 config=kernel_config(raw);assert b.sha(config)==CONFIG_SHA
 for line in [b'CONFIG_MMC_MTK=y',b'CONFIG_MMC_BLOCK=y',b'CONFIG_FAT_FS=y',b'CONFIG_VFAT_FS=y',b'CONFIG_MSDOS_PARTITION=y',b'CONFIG_TMPFS=y']:assert line in config.splitlines()
 cp=b.make_cpio(entries);assert b.parse_cpio(cp)==entries
 gz=bytearray(gzip.compress(cp,compresslevel=9,mtime=0));gz[9]=255;gz=bytes(gz)
 gz+=bytes((-len(gz))%4)
 # Exact length of canonical newc with one 144-byte binding and trailer.
 cap_pos=b.align(110+len('rescue.current.binding')+1,4)
 cap_pos=b.align(cap_pos+144,4)
 cap_size=b.align(b.align(cap_pos+110+len('TRAILER!!!')+1,4),512)
 ram_length=len(gz)+cap_size
 stream=compiled[:-len(dt)];newdt=chosen_dt(dt,ram_length,HEADER)
 mem=check_memory(raw,newdt,ram_length);kernel=b.wrap(kw,stream+newdt)
 h=bytearray(header)
 assert struct.unpack_from('<10I',h,8)[1:]==(0x40080000,struct.unpack_from('<I',h,16)[0],0x44000000,0,0x40f00000,0x4e000000,2048,0,234881318)
 assert len(HEADER)==92
 h[64:576]=HEADER+bytes(512-len(HEADER))
 normalized=bytearray(h);struct.pack_into('<I',normalized,8,len(kernel));normalized[16:20]=bytes(4);normalized[576:608]=bytes(32)
 wrapper=bytearray(rw);wrapper[4:8]=bytes(4)
 binding=b'ASUSC001'+struct.pack('<II',len(kernel),len(gz))+b''.join(bytes.fromhex(b.sha(x)) for x in [normalized,wrapper,kernel,gz])
 assert len(binding)==144
 capsule=b.make_cpio({'rescue.current.binding':(0o100444,0,0,binding)})
 assert len(capsule)==cap_size
 ram=b.wrap(rw,gz+capsule);im=b.make_image(h,kernel,ram)
 h2,k2,r2,tail=b.parse_image(im)
 assert not tail and r2==ram and b.ungzip(k2[512:])[0]==raw and k2[512:512+len(stream)]==stream
 before=parse(dt)[1];after=parse(newdt)[1]
 changes=sorted([n,p] for n in before.keys()|after.keys() for p in before.get(n,{}).keys()|after.get(n,{}).keys() if before.get(n,{}).get(p)!=after.get(n,{}).get(p))
 assert all(n=='/chosen' and p in ('bootargs','linux,initrd-start','linux,initrd-end') for n,p in changes)
 lk=model_lk_gzip(stream+newdt+bytes(512),len(kernel),len(stream),raw)
 return im,gz+capsule,dict(binding_sha256=b.sha(binding),binding_bytes=len(binding),core_gzip_bytes=len(gz),capsule_bytes=len(capsule),kernel_input_sha256=b.sha(compiled),kernel_config_sha256=b.sha(config),compressed_Image_unchanged=True,decompressed_Image_byte_equal=True,dt_changes=changes,header_cmdline=HEADER.decode(),initrd_start=hex(0x44000000),initrd_end=hex(0x44000000+ram_length),initrd_wrapper_stripped=True,memory=mem,LK_gzip_model=lk)
