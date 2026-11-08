"""Recovery-only package using reviewed LK relocation and chosen metadata contract."""
import gzip,struct
import bootformat as b
from fdt import parse
from lk_contract import HEADER,chosen_dt,kernel_config,model_lk_gzip
from boot_memory import check_memory
KERNEL_SHA='e9cde06e85e752aec0433ea37fa926c31b4f7a72cd55453762ec6870e5bb5bf1'
CONFIG_SHA='10b212cabd28aad012582e86c64695ccd450650b4e09ec8da30c21e094f377c2'
def package(init,compiled,header,kw,rw):
 assert len(compiled)==7716897 and b.sha(compiled)==KERNEL_SHA
 raw,dt=b.ungzip(compiled);assert dt
 config=kernel_config(raw);assert b.sha(config)==CONFIG_SHA
 for line in [b'CONFIG_MMC_MTK=y',b'CONFIG_MMC_BLOCK=y',b'CONFIG_FAT_FS=y',b'CONFIG_VFAT_FS=y',b'CONFIG_MSDOS_PARTITION=y',b'CONFIG_TMPFS=y']:assert line in config.splitlines()
 entries={n:(0o40755,0,0,b'') for n in ['dev','proc','sys','sd']};entries['init']=(0o100755,0,0,init)
 cp=b.make_cpio(entries);assert b.parse_cpio(cp)==entries
 gz=bytearray(gzip.compress(cp,compresslevel=9,mtime=0));gz[9]=255;gz=bytes(gz)
 stream=compiled[:-len(dt)];newdt=chosen_dt(dt,len(gz),HEADER)
 # No cmdline initrd token: LK strips the 512-byte wrapper and loads gzip at ramdisk_addr.
 mem=check_memory(raw,newdt,len(gz));ram=b.wrap(rw,gz);kernel=b.wrap(kw,stream+newdt)
 h=bytearray(header);assert struct.unpack_from('<10I',h,8)[1:]==(0x40080000,struct.unpack_from('<I',h,16)[0],0x44000000,0,0x40f00000,0x4e000000,2048,0,234881318)
 h[64:576]=HEADER+bytes(512-len(HEADER));im=b.make_image(h,kernel,ram)
 h2,k2,r2,tail=b.parse_image(im);assert not tail and r2==ram and b.ungzip(k2[512:])[0]==raw and k2[512:512+len(stream)]==stream
 before=parse(dt)[1];after=parse(newdt)[1];changes=sorted([n,p] for n in before.keys()|after.keys() for p in before.get(n,{}).keys()|after.get(n,{}).keys() if before.get(n,{}).get(p)!=after.get(n,{}).get(p))
 assert changes==[['/chosen','bootargs'],['/chosen','linux,initrd-end'],['/chosen','linux,initrd-start']]
 lk=model_lk_gzip(stream+newdt+bytes(512),len(kernel),len(stream),raw)
 return im,cp,gz,{'kernel_input_sha256':b.sha(compiled),'kernel_config_sha256':b.sha(config),'compiled_Image_sha256':b.sha(raw),'compiled_Image_bytes':len(raw),'compressed_Image_sha256':b.sha(stream),'compressed_Image_unchanged':True,'decompressed_Image_byte_equal':True,'dt_before_sha256':b.sha(dt),'dt_after_sha256':b.sha(newdt),'dt_changes':changes,'header_cmdline':HEADER.decode(),'initrd_start':hex(0x44000000),'initrd_end':hex(0x44000000+len(gz)),'initrd_wrapper_stripped':True,'memory':mem,'LK_gzip_model':lk}
