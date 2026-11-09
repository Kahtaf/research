#!/usr/bin/env python3
"""Offline-only stock-kernel recovery capsule builder; never opens a device."""
from pathlib import Path
import gzip, hashlib, json, stat, struct, tarfile

HERE=Path(__file__).resolve().parents[1]
OUT=HERE/'artifacts/recovery-capsule'
STOCK=HERE.parent/'2026-11-06-asus-local-stock-rollback/artifacts/stock-rollback'
PART=0xff7000
BOOT_SHA='7bb68511b1ade34d24c3e932da7260e6753fa87270bd8249a7218755a5df3316'
REC_SHA='902b2f06a01cca574b4aa374e67c4e7f8f0ed53f6e6a55017b6d96351f0f1f20'
ALP_SHA='4b14c18f7e90a063b61462ea1462a5732c154bf6adad594974fe6487cd98a8de'
sha=lambda b:hashlib.sha256(b).hexdigest()
def pad(b,n=2048):return b+bytes(-len(b)%n)
def image_id(k,r):return hashlib.sha1(k+struct.pack('<I',len(k))+r+struct.pack('<II',len(r),0)).digest()+bytes(12)
def parse(b,expected_name):
 assert len(b)==PART and b[:8]==b'ANDROID!'
 ks,ka,rs,ra,ss,sa,ta,page=struct.unpack_from('<8I',b,8)
 assert page==2048 and ss==0
 ro=page+len(pad(bytes(ks)))
 k,r=b[page:page+ks],b[ro:ro+rs]
 assert b[576:608]==image_id(k,r)
 for blob,name in ((k,b'KERNEL'),(r,expected_name)):
  assert blob[:4]==bytes.fromhex('88168858')
  assert blob[8:40].split(b'\0')[0]==name
  assert struct.unpack_from('<I',blob,4)[0]==len(blob)-512
 return b[:page],k,r

def cpio(entries):
 out=bytearray()
 for ino,(name,mode,data,major,minor) in enumerate(entries+[('TRAILER!!!',0,b'',0,0)],1):
  nb=name.encode()+b'\0';nlinks=2 if stat.S_ISDIR(mode) else 1
  fields=[ino,mode,0,0,nlinks,0,len(data),0,0,major,minor,len(nb),0]
  out+=b'070701'+''.join(f'{v:08x}' for v in fields).encode()+nb
  out=bytearray(pad(out,4));out+=data;out=bytearray(pad(out,4))
 return pad(out,512)

def elf_needed(b):
 assert b[:6]==b'\x7fELF\x02\x01' and struct.unpack_from('<H',b,18)[0]==183
 off=struct.unpack_from('<Q',b,32)[0];entsize,num=struct.unpack_from('<HH',b,54)
 ph=[struct.unpack_from('<IIQQQQQQ',b,off+i*entsize) for i in range(num)]
 dyn=next(x for x in ph if x[0]==2)
 d=[struct.unpack_from('<qQ',b,pos) for pos in range(dyn[2],dyn[2]+dyn[5],16)]
 st=next(v for k,v in d if k==5)
 so=next(x[2]+st-x[3] for x in ph if x[0]==1 and x[3]<=st<x[3]+x[5])
 needed=[b[so+v:b.index(b'\0',so+v)].decode() for k,v in d if k==1]
 interp=next(x for x in ph if x[0]==3)
 return b[interp[2]:interp[2]+interp[5]].rstrip(b'\0').decode(),needed

def verify_cpio(raw,expected):
 pos=0;found={}
 while True:
  assert raw[pos:pos+6]==b'070701'
  f=[int(raw[pos+6+8*i:pos+14+8*i],16) for i in range(13)]
  nb=raw[pos+110:pos+110+f[11]];assert nb[-1:]==b'\0';name=nb[:-1].decode()
  pos=(pos+110+f[11]+3)&~3
  value=raw[pos:pos+f[6]];pos=(pos+f[6]+3)&~3
  if name=='TRAILER!!!':break
  assert name not in found and name and not name.startswith('/') and '..' not in name.split('/')
  found[name]=(f[1],value,f[9],f[10])
 assert not any(raw[pos:])
 assert found=={n:(m,v,ma,mi) for n,m,v,ma,mi in expected}
 return len(found)

def main():
 boot=(STOCK/'boot.img').read_bytes();rec=(STOCK/'recovery.img').read_bytes()
 assert sha(boot)==BOOT_SHA and sha(rec)==REC_SHA
 _,kernel,_=parse(boot,b'ROOTFS');header,rec_kernel,old_ramdisk=parse(rec,b'RECOVERY')
 assert kernel==rec_kernel,'Exact original boot and recovery kernels differ'
 tar_path=HERE/'downloads/alpine-minirootfs-3.24.4-aarch64.tar.gz'
 assert sha(tar_path.read_bytes())==ALP_SHA
 with tarfile.open(tar_path) as t:
  bb=t.extractfile('./bin/busybox').read();musl=t.extractfile('./lib/ld-musl-aarch64.so.1').read()
 interp,needed=elf_needed(bb)
 assert interp=='/lib/ld-musl-aarch64.so.1' and needed==['libc.musl-aarch64.so.1'],(interp,needed)
 required=['sh','mount','umount','mknod','mkdir','mdev','cat','cut','sha256sum','tar','switch_root','setsid','su','timeout','losetup','stat','dd','od','tr']
 assert all(b'\0'+n.encode()+b'\0' in bb for n in required),'Missing required bootstrap applet'
 entries=[]
 for d in ['bin','sbin','lib','dev','dev/pts','dev/input','proc','sys','run','mnt','mnt/sd','newroot','capsule']:
  entries.append((d,stat.S_IFDIR|0o755,b'',0,0))
 entries.extend([
  ('bin/busybox',stat.S_IFREG|0o755,bb,0,0),
  ('bin/sh',stat.S_IFLNK|0o777,b'busybox',0,0),
  ('lib/ld-musl-aarch64.so.1',stat.S_IFREG|0o755,musl,0,0),
  ('lib/libc.musl-aarch64.so.1',stat.S_IFLNK|0o777,b'ld-musl-aarch64.so.1',0,0),
  ('dev/console',stat.S_IFCHR|0o600,b'',5,1),
 ])
 for dest,src in [('init','recovery-init.sh'),('capsule/sysinit','recovery-sysinit.sh'),('capsule/start-desktop','recovery-start-desktop.sh'),('capsule/serial-login','recovery-serial-login.sh'),('capsule/udhcpc','recovery-udhcpc.sh'),('capsule/wmt-property-area.py','wmt-property-area.py'),('capsule/validate-wmt-loader.py','recovery-validate-wmt-loader.py'),('capsule/state.py','recovery-state.py')]:
  entries.append((dest,stat.S_IFREG|0o755,(HERE/'scripts'/src).read_bytes(),0,0))
 raw=cpio(entries);count=verify_cpio(raw,entries);compressed=gzip.compress(raw,compresslevel=6,mtime=0)
 wrapper=bytearray(old_ramdisk[:512]);struct.pack_into('<I',wrapper,4,len(compressed));rd=bytes(wrapper)+compressed
 h=bytearray(header);struct.pack_into('<I',h,8,len(kernel));struct.pack_into('<I',h,16,len(rd));h[576:608]=image_id(kernel,rd)
 result=bytes(h)+pad(kernel)+pad(rd);assert len(result)<=PART
 full=result+bytes(PART-len(result));oh,ok,orr=parse(full,b'RECOVERY')
 assert ok==kernel and orr==rd and gzip.decompress(orr[512:])==raw
 allowed=set(range(16,20))|set(range(576,608))
 changed=[i for i,(a,b) in enumerate(zip(header,oh)) if a!=b]
 assert set(changed)<=allowed
 OUT.mkdir(parents=True,exist_ok=True)
 (OUT/'recovery-alpine-stock-ram.img').write_bytes(full)
 (OUT/'ramdisk.cpio.gz').write_bytes(compressed)
 manifest={
  'status':'OFFLINE_BUILT_NOT_BOOTED_OR_DEPLOYED',
  'image_file':'recovery-alpine-stock-ram.img','image_bytes':len(full),'image_used_bytes':len(result),'image_sha256':sha(full),
  'original_boot_sha256':BOOT_SHA,'original_recovery_sha256':REC_SHA,
  'kernel_wrapped_bytes':len(kernel),'kernel_wrapped_sha256':sha(kernel),'kernel_payload_sha256':sha(kernel[512:]),
  'kernel_byte_identical_to_original_boot':True,'kernel_byte_identical_to_original_recovery':True,
  'header_source':'canonical stock recovery; only ramdisk size and image ID changed','header_changed_offsets':changed,
  'ramdisk_mtk_name':'RECOVERY','ramdisk_compressed_bytes':len(compressed),'cpio_entries':count,
  'bootstrap_busybox_sha256':sha(bb),'bootstrap_musl_sha256':sha(musl),'bootstrap_interpreter':interp,'bootstrap_dt_needed':needed,
  'alpine_minirootfs_sha256':ALP_SHA,
  'sd_directory':'/2026-11-08-asus-alpine','sd_marker':'ALPINE.ID = asus-alpine-stock-kernel-v1',
  'root_marker':'/etc/asus-alpine-ram-release = asus-alpine-stock-kernel-v1',
  'root_archive':'alpine-3.24.4-ram-rootfs.tar.gz','root_archive_checksum':'alpine-3.24.4-ram-rootfs.tar.gz.sha256',
  'automatic_cold_wifi':'manual COLD-WIFI.ENABLE=asus-alpine-stock-wmt-v1; exactly one successful module-init ioctl plus stpwmt class required before ready=yes',
  'property_gate_status':'sealed property gate and prior independent RAM-root cold WMT/WiFi/SSH physically proved by parent; optional SD-loop root revision unbooted',
  'property_area_generator_sha256':sha((HERE/'scripts/wmt-property-area.py').read_bytes()),
  'wmt_ready_rule':'one ioctl request 0x80047704 returning 0 AND one live stpwmt sysfs class; loader exit status is not readiness',
  'chipid_override':False,
  'storage_writes':'SYSTEM ro,noload; SD ro by default, optional marked state and 2GiB ext4-loop OS file; runtime logs/devices tmpfs',
  'optional_sd_persistence':'PERSISTENCE.ENABLE=asus-alpine-state-v1; protected rw SD, own service-data bind, stable host key, loopback dashboard',
  'persistence_helper_sha256':sha((HERE/'scripts/recovery-state.py').read_bytes()),
  'optional_sd_root':'ROOT.EXT4.ENABLE=asus-alpine-ext4-root-v1 plus PERSISTENCE.ENABLE=asus-alpine-state-v1; fixed regular2GiB alpine-root.ext4; protected SD rw, unused sysfs-derived loop, ext4 rw,noatime',
  'sd_root_image_bytes':2*1024*1024*1024,
  'root_mode_evidence':'/run/asus-alpine/root-mode: RAM or SD-loop; /run/asus-alpine/root-loop-device in SD-loop mode',
  'sd_root_failure':'enabled but invalid image/loop/mount/marker enters rescue, never falls back to archive',
  'root_tmpfs_limit_bytes':768*1024*1024,
 }
 (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print(json.dumps(manifest,indent=2))
if __name__=='__main__':main()
