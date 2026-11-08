#!/usr/bin/env python3
"""Check the real sparse ext4 image without mounting it or accessing a device."""
import hashlib,json,struct,subprocess,sys
from ext4_features import inspect
from pathlib import Path
root=Path('/srv/android/lineage24');out=root/'out/target/product/p00a';host=root/'out/host/linux-x86/bin'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
image=out/'system.img';digest=sha(image)
work=Path('/srv/android/asus-build-integration/image-inspection')/digest[:16];work.mkdir(parents=True,exist_ok=True)
raw=work/'system.raw.img'
if not raw.exists():
 with image.open('rb') as f: sparse=f.read(4)==bytes.fromhex('3aff26ed')
 if sparse:subprocess.run([str(host/'simg2img'),str(image),str(raw)+'.partial'],check=True)
 else:
  import shutil;shutil.copyfile(image,str(raw)+'.partial')
 Path(str(raw)+'.partial').rename(raw)
with raw.open('rb') as f:
 f.seek(1024);sb=f.read(1024)
assert sb[56:58]==b'\x53\xef'
block=1024<<struct.unpack_from('<I',sb,24)[0];blocks=struct.unpack_from('<I',sb,4)[0]
features=struct.unpack_from('<III',sb,92)
feature_check=inspect(bytes(1024)+sb)
if features[1]&0x80:blocks|=struct.unpack_from('<I',sb,336)[0]<<32
assert block*blocks==raw.stat().st_size
assert raw.stat().st_size<=3753902080
check=subprocess.run([str(host/'e2fsck'),'-fn',str(raw)],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
(work/'e2fsck.log').write_text(check.stdout)
assert check.returncode==0,check.stdout
listing=subprocess.run([str(host/'debugfs'),'-R','ls -p /',str(raw)],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
(work/'root-listing.txt').write_text(listing.stdout)
paths=['system/bin/init','system/etc/init/hw/init.rc','system/vendor/etc/fstab.mt8163','system/vendor/bin/hw/android.hardware.health-service.asus-p00a','system/framework/services.jar','system/product/etc/security/adb_keys']
google=json.loads(Path('/srv/android/asus-device-product/google-inline/evidence/inline-source-manifest.json').read_text())
paths+=list(google['payload_members'])
checks=[]
for i,name in enumerate(paths):
 dump=work/('file-'+str(i))
 p=subprocess.run([str(host/'debugfs'),'-R',f'dump /{name} {dump}',str(raw)],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 assert p.returncode==0 and dump.is_file(),(name,p.stdout)
 actual=sha(dump);expected=sha(out/name)
 assert actual==expected,name
 if name in google['payload_members']:assert actual==google['payload_members'][name]['sha256'],name
 checks.append(dict(path='/'+name,sha256=actual,bytes=dump.stat().st_size))
 dump.unlink()
r=dict(system_image_sha256=digest,raw_image=str(raw),filesystem_bytes=raw.stat().st_size,physical_gpt_partition_bytes=3753902080,block_bytes=block,kernel_ext4_feature_check=feature_check,e2fsck=dict(exit_code=check.returncode,output=check.stdout),root_listing=listing.stdout,files_verified_inside_image=checks,device_accessed=False)
Path(sys.argv[1]).write_text(json.dumps(r,indent=2)+'\n')
print('Actual image ext4 check, root layout, and',len(checks),'file hashes passed.')
