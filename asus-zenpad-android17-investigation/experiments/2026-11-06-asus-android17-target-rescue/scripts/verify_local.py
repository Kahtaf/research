"""Verify the delivered image, compiled policy/context pins, source pins and manifest.
Runs offline on macOS or Linux; no device, network or mutation operations.
"""
import hashlib,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'source'))
from bootformat import parse_image,parse_cpio,ungzip,elf_static,sha,RECOVERY_SHA,PARTITION_SIZE
from client import parse

def main():
 candidate=R/'artifacts/candidate-delivery'
 report=json.loads((candidate/'build.json').read_text())
 contract=json.loads((candidate/'session-contract.UNAPPROVED.json').read_text())
 raw=(candidate/'UNTESTED-target-rescue.p10.raw').read_bytes()
 image=(candidate/'UNTESTED-target-rescue.img').read_bytes()
 assert len(raw)==PARTITION_SIZE and raw==image+bytes(PARTITION_SIZE-len(image))
 assert sha(raw)==contract['p10_full_sha256'] and sha(image)==report['image_sha256']
 header,kernel,ramdisk,_=parse_image(image)
 stock=(R/'inputs/initial/recovery.bin').read_bytes()
 assert sha(stock)==RECOVERY_SHA and stock==(R/'inputs/verify/recovery.bin').read_bytes()
 assert kernel==parse_image(stock)[1]
 assert b'androidboot.selinux=enforcing' in header and b'androidboot.selinux=permissive' not in header
 entries=parse_cpio(ungzip(ramdisk[512:])[0])
 assert set(entries)==set(report['entries'])
 for name,(mode,uid,gid,data) in entries.items():
  expected=report['entries'][name]
  assert (oct(mode),uid,gid,len(data),sha(data))==(expected['mode'],expected['uid'],expected['gid'],expected['bytes'],expected['sha256']),name
 for name in ['sbin/os-rescue','sbin/rescue-proxy','system/bin/sh']:
  elf_static(entries[name][3])
 assert entries['system/bin/sh'][3]==entries['sbin/rescue-proxy'][3]
 assert entries['sbin/os-rescue'][3]==(R/'artifacts/tools-delivery/os-rescue').read_bytes()
 manifest=entries['rescue.manifest'][3]
 assert manifest==(candidate/'rescue.manifest').read_bytes() and not parse(manifest)
 assert contract['armed'] is False and contract['userdata_enabled'] is False
 assert contract['mode']=='PARENT_REVIEW_REQUIRED' and contract['physical_validation'] is False
 plan=json.loads((R/'artifacts/stock-inverse.PLAN_ONLY.json').read_text())
 assert manifest[16:48].hex()==plan['cid_sha256']
 assert manifest[48:80].hex()==plan['primary_gpt_sha256']
 assert manifest[80:112].hex()==plan['backup_gpt_sha256']
 assert plan['write_authorized'] is False and plan['userdata_authorized'] is False and not plan['install_images']
 assert entries['file_contexts.bin'][3]==(candidate/'file_contexts.bin').read_bytes()
 assert entries['sepolicy'][3]==(candidate/'rescue-sepolicy').read_bytes()
 rc=entries['init.rc'][3].decode()
 assert '    oneshot\n' in rc.split('service os-rescue ',1)[1].split('service adbd ',1)[0]
 for forbidden in ['reboot','powerctl','deadline','import ','mount_all','exec ']:
  assert all(forbidden not in l for l in rc.splitlines() if not l.lstrip().startswith('#')),forbidden
 for path,digest in report['sources'].items():
  if path.startswith('._'):continue  # Remote AppleDouble metadata is not compiler input.
  assert sha((R/'source'/path).read_bytes())==digest,path
 for path,digest in json.loads((R/'SOURCE_PINS.json').read_text())['source_files'].items():
  assert sha((R/path).read_bytes())==digest,path
 local=json.loads((R/'artifacts/local-stock-inverse.PLAN_ONLY.json').read_text())
 assert local['write_authorized'] is False and local['userdata_authorized'] is False
 assert sha((R/'inputs/parent/local-stock-rollback.READY.json').read_bytes())==local['receipt_sha256']
 for row in local['images'].values():
  assert Path(row['path']).stat().st_size==row['bytes']
 review=json.loads((R/'artifacts/parent-review.PENDING.json').read_text())
 assert list(review['images'])==['original_system','original_boot'] and review['approvals']['independent_rescue_review'] is False
 for line in (R/'SHA256SUMS').read_text().splitlines():
  digest,name=line.split('  ',1)
  assert sha((R/name).read_bytes())==digest,name
 print(json.dumps({'passed':True,'image_sha256':sha(image),'p10_sha256':sha(raw),
                   'manifest_records':len(parse(manifest)),'cid_hash_pinned':True,
                   'stock_kernel_identical':True,'no_device_operations':True},indent=2))
if __name__=='__main__':main()
