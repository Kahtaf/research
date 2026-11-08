"""Final byte join only. Never creates image admissions, arm IDs or helper pins."""
from pathlib import Path
import argparse,sys,os,stat,struct,json,gzip,hashlib
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'source'))
import bootformat as b
from package_core import package

def ordinary(path,limit):
 fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
 try:
  st=os.fstat(fd)
  if not stat.S_ISREG(st.st_mode) or st.st_size>limit:raise ValueError('bounded ordinary input required: '+str(path))
  data=b''
  while len(data)<st.st_size:
   x=os.read(fd,st.st_size-len(data))
   if not x:raise ValueError('short input')
   data+=x
  after=os.fstat(fd)
  if (after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns)!=(st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns,st.st_ctime_ns):raise ValueError('input changed during read')
  return data
 finally:os.close(fd)

def five_roles(data):
 # The parent supplies the real admission product. No raw images are reread here.
 if len(data)<112 or data[:8]!=b'ASUSR002' or struct.unpack_from('<II',data,8)!=(2,5):raise ValueError('genuine admitted five-role ASUSR002 manifest required')
 if data[16:48]==bytes(32) or data[48:80].hex()!='f87e70586706b06d029a2bc8521f1b8ae9176873cba1e5b4281cbaca816742ae' or data[80:112].hex()!='2bf991125a74bf360d0cf4eb217df369ba2f78acf3dd312f26dc7695d2f31784':raise ValueError('actual CID/GPT authority required')
 off=112;rows=[]
 for role in range(5):
  if off+52>len(data):raise ValueError('short role')
  index,part,size=struct.unpack_from('<IIQ',data,off);whole=data[off+16:off+48];count=struct.unpack_from('<I',data,off+48)[0]
  expected_part=26 if role==4 else 9 if role%2 else 25
  expected_size={9:16740352,25:3753902080,26:11331268096}[expected_part]
  if (index,part,size,count)!=(role,expected_part,expected_size,(expected_size+1048575)//1048576):raise ValueError('fixed role geometry/chunk count required')
  off+=52;end=off+32*count
  if end>len(data) or whole==bytes(32) or any(data[n:n+32]==bytes(32) for n in range(off,end,32)):raise ValueError('actual full/chunk hashes required')
  if role==1 and whole.hex()!='7bb68511b1ade34d24c3e932da7260e6753fa87270bd8249a7218755a5df3316':raise ValueError('exact original BOOT required')
  rows.append(dict(role=role,part=part,bytes=size,chunks=count,sha256=whole.hex()));off=end
 if off!=len(data):raise ValueError('manifest trailing bytes')
 if rows[0]['sha256']==rows[2]['sha256'] or rows[1]['sha256']==rows[3]['sha256']:raise ValueError('actual install pair required')
 return rows

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--manifest',type=Path,required=True);p.add_argument('--arm-file',type=Path,required=True)
 p.add_argument('--kernel',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True)
 a=p.parse_args()
 manifest=ordinary(a.manifest,1024**2);roles=five_roles(manifest)
 arm=ordinary(a.arm_file,65)
 if len(arm)!=65 or arm[-1:]!=b'\n' or any(c not in b'0123456789abcdef' for c in arm[:64]) or arm[:64]==b'0'*64:raise ValueError('parent actual arm ID must be 64 lowercase hex plus LF')
 pins=json.loads((R/'evidence/DELIVERY_PINS.json').read_text())
 for rel,pin in pins.items():
  if b.sha((R/rel).read_bytes())!=pin:raise ValueError('delivered assembly input changed: '+rel)
 common=ordinary(R/'artifacts/common-rootfs.cpio.gz',4*1024**2);e=b.parse_cpio(gzip.decompress(common))
 assert 'rescue.manifest' not in e and 'rescue.sd.arm' not in e
 assert b'start rescue-sd-offline' not in e['init.rc'][3]
 e['rescue.manifest']=(0o100444,0,0,manifest);e['rescue.sd.arm']=(0o100444,0,0,arm)
 action=(R/'source/init.offline.action.rc').read_bytes()
 e['init.rc']=(0o100644,0,0,e['init.rc'][3]+b'\n'+action)
 assert e['init.rc'][3].count(b'start rescue-sd-offline')==1
 for n in ['sbin/p10-restore','system/bin/sh','sbin/adbd']:assert n not in e
 k=ordinary(a.kernel,8*1024**2)
 im,gz,contract=package(e,k,(R/'inputs/original-header').read_bytes(),(R/'inputs/original-kernel-wrapper').read_bytes(),(R/'inputs/original-wrapper').read_bytes())
 # Refuse an existing destination. No deployment, raw writer or card mutation.
 a.output_dir.mkdir()
 def write(name,data):
  with (a.output_dir/name).open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
 write('candidate.img',im);padded=im+bytes(b.PARTITION_SIZE-len(im));write('candidate.p10.raw',padded)
 write('operational-rootfs.cpio.gz',gz)
 trigger=b'OFFLINE-PREARMED ASUSR002 '+b.sha(manifest).encode()+b' '+arm[:64]+b' install:2,4,3\n'
 write('execute.trigger',trigger)
 receipt=dict(status='ASSEMBLED_NOT_PHYSICALLY_QUALIFIED',manifest_sha256=b.sha(manifest),arm_id=arm[:64].decode(),roles=roles,image_sha256=b.sha(im),image_bytes=len(im),p10_sha256=b.sha(padded),p10_bytes=len(padded),packaging=contract,normal_graph_keeps_custom_recovery=True,original_recovery_helper_included=False,physical_boot_verified=False,sd_hardware_verified=False)
 write('assembly.json',(json.dumps(receipt,indent=2)+'\n').encode())
 d=os.open(a.output_dir,os.O_RDONLY|os.O_DIRECTORY);os.fsync(d);os.close(d)
 print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
