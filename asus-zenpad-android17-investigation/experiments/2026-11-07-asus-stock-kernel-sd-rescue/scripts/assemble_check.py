"""Parent-local CHECK join only; real manifest and existing arm are required."""
from pathlib import Path
import argparse,gzip,json,os,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'source'))
import bootformat as b
from package_core import package,KERNEL_SHA
from final_package import ordinary,five_roles
EXPECTED_MANIFEST_SHA='9fe4ec15800257262092f11698525939ebdfb404e150fbc7d308c7f8280ba534'
STOCK=R.parent/'2026-11-05-asus-boot-access-audit/artifacts/device-backup/initial/recovery.bin'
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--manifest',type=Path,required=True);p.add_argument('--arm-file',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args()
 manifest=ordinary(a.manifest,1024**2);roles=five_roles(manifest)
 if b.sha(manifest)!=EXPECTED_MANIFEST_SHA:raise ValueError("parent-reported actual five-role manifest identity required")
 original=ordinary(R/'inputs/original-stock.manifest',128*1024)
 if b.sha(original)!='605cdec038dafe3dddabfe92b8bd6cd189734f740230dfc362d02a43421e4e47' or manifest[16:112]!=original[16:112] or manifest[112:len(original)]!=original[112:]:raise ValueError('exact original manifest prefix required')
 arm=ordinary(a.arm_file,65)
 if len(arm)!=65 or arm[-1:]!=b'\n' or any(c not in b'0123456789abcdef' for c in arm[:64]) or arm[:64]==b'0'*64:raise ValueError('existing actual parent arm ID required')
 for rel,pin in json.loads((R/'evidence/DELIVERY_PINS.json').read_text()).items():
  if b.sha(ordinary(R/rel,8*1024**2))!=pin:raise ValueError('delivery changed: '+rel)
 stock=ordinary(STOCK,b.PARTITION_SIZE)
 if len(stock)!=b.PARTITION_SIZE or b.sha(stock)!=b.RECOVERY_SHA:raise ValueError('exact original recovery required')
 h,k,rd,_=b.parse_image(stock)
 if b.sha(k)!=KERNEL_SHA:raise ValueError('stock wrapped kernel mismatch')
 for n,d in [('original-header',h),('original-kernel-wrapper',k[:512]),('original-wrapper',rd[:512])]:
  if ordinary(R/'inputs'/n,2048)!=d:raise ValueError('original input mismatch: '+n)
 e=b.parse_cpio(gzip.decompress(ordinary(R/'artifacts/common-rootfs.cpio.gz',4*1024**2)))
 assert 'rescue.manifest' not in e and 'rescue.sd.arm' not in e
 init=e['init.rc'][3].split(b'service rescue-sd-offline',1)[0].replace(b'/sbin/p10-restore ',b'')
 assert b'start rescue-sd-offline' not in init
 init+=b'\n'+ordinary(R/'source/init.check.action.rc',4096)
 e['init.rc']=(0o100644,0,0,init)
 e['sbin/rescue-sd']=(0o100755,0,0,ordinary(R/'artifacts/rescue-sd-check',2*1024**2))
 e['sbin/rescue-sd-supervisor']=(0o100700,0,0,ordinary(R/'artifacts/rescue-sd-check-runner',2*1024**2))
 e.pop('sbin/p10-restore')
 e['rescue.manifest']=(0o100444,0,0,manifest);e['rescue.sd.arm']=(0o100444,0,0,arm)
 assert all(x not in init for x in [b'--execute',b'--offline-',b'stock-restore',b'start rescue-sd-offline'])
 assert not any(n in e for n in ['system/bin/sh','sbin/adbd','sbin/p10-restore'])
 im,members,contract=package(e,k,h,k[:512],rd[:512]);padded=im+bytes(b.PARTITION_SIZE-len(im))
 a.output_dir.mkdir()
 def write(n,d):
  with (a.output_dir/n).open('xb') as f:f.write(d);f.flush();os.fsync(f.fileno())
 write('candidate.img',im);write('candidate.p10.raw',padded);write('check-ramdisk.members',members)
 write('manifest.sha256',b.sha(manifest).encode()+b'\n')
 receipt=dict(status='CHECK_ONLY_ASSEMBLED_NOT_PHYSICALLY_QUALIFIED',manifest_sha256=b.sha(manifest),arm_id=arm[:64].decode(),roles=roles,image_bytes=len(im),image_sha256=b.sha(im),p10_bytes=len(padded),p10_sha256=b.sha(padded),packaging=contract,report='SDCHECK.TXT',report_limit_bytes=16384,plan_deadline_seconds=600,uid=2000,context='u:r:shell:s0',daemon_requests='STATUS only; enforced by CHECK frontend',write_requests=False,selectors_or_triggers_emitted=False,normal_reboot_after_success=True,physical_boot_verified=False)
 write('assembly.json',(json.dumps(receipt,indent=2)+'\n').encode());d=os.open(a.output_dir,os.O_RDONLY|os.O_DIRECTORY);os.fsync(d);os.close(d)
 print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
