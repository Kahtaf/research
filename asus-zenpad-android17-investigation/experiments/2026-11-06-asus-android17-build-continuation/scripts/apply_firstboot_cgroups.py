#!/usr/bin/env python3
import pathlib,hashlib,shutil,subprocess,json,datetime
R=pathlib.Path('/srv/android/asus-build-continuation');K=R/'kernel';F=pathlib.Path('/srv/android/asus-firstboot-runtime/stagedpatches');O=R/'inputs/firstboot-cgroups-r1';O.mkdir()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
patches={'blkio/0001-enable-blkio-cgroup.patch':'b13f28962f985a0c50c8c5599ac6730df9361e6bc486fe4fb194ec4137df602f','cpuset-v2/0002-cpuset-v2-mode-backport.patch':'8290f3f6ebbfa81c630c76730b4bec701679995fcc502ef4666f8b050f941163'}
for name in ['blkio','cpuset-v2']:
    shutil.copytree(F/name,O/name)
    assert sha(F/name/'manifest.json')==sha(O/name/'manifest.json')
for rel,h in patches.items():assert sha(F/rel)==sha(O/rel)==h
blk=json.loads((O/'blkio/manifest.json').read_text());cpu=json.loads((O/'cpuset-v2/manifest.json').read_text())
files=[{'path':'arch/arm64/configs/asus_p00a_defconfig','before_sha256':blk['before_sha256'],'after_sha256':blk['after_sha256']},*cpu['files']]
assert {x['path'] for x in files}=={'arch/arm64/configs/asus_p00a_defconfig','include/linux/cgroup-defs.h','kernel/cgroup.c','kernel/cpuset.c'}
for entry in files:assert sha(K/entry['path'])==entry['before_sha256'],entry
for rel in patches:subprocess.run(['git','-C',str(K),'apply','--check',str(O/rel)],check=True)
assert sha(R/'build/arch/arm64/boot/Image.gz-dtb')=='84007607154fd2b7d5f69dff63a1474589d2b6ddd0086511ff1cca4f34ebd59f'
archive=R/'artifacts/combined-kernel-r3'
for rel in ['evidence/combined-from-active-soc.patch','artifacts/combined-source-changes.tar.gz']:
    src=R/rel;dst=archive/src.name;assert not dst.exists();shutil.copyfile(src,dst)
shutil.copyfile(R/'build/.config',O/'combined-before.config')
for rel in patches:subprocess.run(['git','-C',str(K),'apply',str(O/rel)],check=True)
for entry in files:assert sha(K/entry['path'])==entry['after_sha256'],entry
subprocess.run([str(K/'scripts/config'),'--file',str(R/'build/.config'),'--enable','BLK_CGROUP'],check=True)
record={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'patches':patches,'files':files,'source_preimages_and_postimages_verified':True,'active_aosp_or_kernel_changed':False,'parent_reported_qualification':'firstboot run-boot-r9 genuine SDK37 SetupCgroups succeeded, ueventd coldboot, enforcing property checks; cpuset positive r2 13 checks; no crypto/APEX/auth-adbd claim','unchanged_sdk37_cgroups_json_sha256':'ab2ed667ff45958843fb0c6ee953a5512def0ae87470c4358aa9576a6a4b2e22','physical_boot_verified':False}
(R/'evidence/firstboot-cgroups-applied.json').write_text(json.dumps(record,indent=2)+'\n');print('Qualified cgroup patches applied only to isolated combined fixture; four exact pre/post images verified.')
