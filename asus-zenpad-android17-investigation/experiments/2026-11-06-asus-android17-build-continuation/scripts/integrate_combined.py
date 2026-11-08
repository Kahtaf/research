#!/usr/bin/env python3
"""Serialize combined integration only after the real prior full job terminates."""
import argparse,pathlib,json,hashlib,subprocess,fcntl,shutil,os,datetime
R=pathlib.Path('/srv/android/asus-build-continuation');A=pathlib.Path('/srv/android/lineage24');K=pathlib.Path('/srv/android/asus-android17/kernel-bpf-fd');P=pathlib.Path('/srv/android/asus-device-product');D=A/'device/asus/p00a'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def manifest(root):return {str(p.relative_to(root)):({'symlink':str(p.readlink())} if p.is_symlink() else {'sha256':sha(p)}) for p in sorted(root.rglob('*')) if p.is_file() or p.is_symlink()}
a=argparse.ArgumentParser();a.add_argument('--apply',action='store_true');args=a.parse_args()
lock=(P/'logs/full-product-build.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
for marker in ['exit-code','finished']:assert (P/('logs/full-build-r5.'+marker)).is_file(),'Original r5 has no genuine terminal marker'
for process in ['soong_ui','soong_build','ckati','siso']:
 assert subprocess.run(['pgrep','-x',process],stdout=subprocess.DEVNULL).returncode==1,'Build process remains live: '+process
release=json.loads((R/'evidence/combined-release.json').read_text());source=json.loads((R/'evidence/combined-source-receipt.json').read_text());product=json.loads((R/'evidence/product-staging.json').read_text());baseline=json.loads((R/'evidence/snapshot.json').read_text())
network=json.loads((R/'evidence/network-staging.json').read_text());network_kernel=json.loads((R/'evidence/network-kernel-applied.json').read_text())
qualified=json.loads((R/'evidence/qualified-combined-inputs.json').read_text())
assert qualified['firstboot_file_locking_parity_accepted'] and qualified['targeted_network_handoff_accepted']
assert qualified['combined_kernel_sha256']==release['image']['sha256']
image=R/'build/arch/arm64/boot/Image.gz-dtb';config=R/'build/.config';patch=R/'evidence/combined-from-active-soc.patch'
kernel_release=(R/'build/include/config/kernel.release').read_text().strip();assert kernel_release.startswith('4.9.') and '\n' not in kernel_release
assert sha(image)==release['image']['sha256']==source['compiled_kernel_sha256'];assert sha(config)==release['config_sha256'];assert sha(patch)==source['patch_sha256']
config_text=config.read_text()
for symbol in ['BLK_CGROUP','FILE_LOCKING']:assert f'CONFIG_{symbol}=y\n' in config_text,symbol
for symbol in ['DUMMY','VETH','NAMESPACES','NET_NS']:assert f'CONFIG_{symbol}=y\n' not in config_text,symbol
assert all(sha(K/p)==h for p,h in baseline['files'].items()),'Frozen active kernel changed'
assert manifest(D)==product['before'],'Frozen active device product changed'
assert sha(A/'system/connectivity/wificond/wificond.rc')==product['wificond_before_sha256']
for p,c in source['changes'].items():assert sha(R/'kernel'/p)==c['after']
for p,c in network['kernel_preimages_verified'].items():assert sha(R/'kernel'/p)==c['tested_sha256']
for p,h in network['connectivity_before'].items():assert sha(A/'packages/modules/Connectivity'/p)==h
for p,h in network['connectivity_after'].items():assert sha(R/'platform-connectivity'/p)==h
candidate_manifest=manifest(R/'product-device')
for p,c in product['changes'].items():assert candidate_manifest[p]==c['after']
subprocess.run(['git','-C',str(K),'apply','--check','--whitespace=nowarn',str(patch)],check=True)
defconfig=K/'arch/arm64/configs/asus_p00a_combined_defconfig';assert not defconfig.exists()
if not args.apply:print('Terminal job, lock, source/product preimages and all pinned artifacts verified; no changes');raise SystemExit(0)
receipt=R/'evidence/active-integration.json';assert not receipt.exists()
archive=R/'artifacts/full-r5-before-integration';archive.mkdir()
for name in ['boot.img','system.img','ramdisk.img']:
 f=A/'out/target/product/p00a'/name
 if f.exists():subprocess.run(['cp','--reflink=auto',str(f),str(archive/name)],check=True)
for f in (P/'logs').glob('full-build-r5.*'):shutil.copy2(f,archive/f.name)
for p in network['connectivity_before']:
 target=archive/'Connectivity'/p;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(A/'packages/modules/Connectivity'/p,target)
subprocess.run(['git','-C',str(K),'apply','--whitespace=nowarn',str(patch)],check=True)
for p,c in source['changes'].items():assert sha(K/p)==c['after']
# Generated defconfig is EXACTLY the config used for the compiled prebuilt.
# Keep the compiled fixture unchanged; the active header generator selects this copy.
defconfig.write_bytes(config.read_bytes())
for p,c in product['changes'].items():
 target=D/p;target.parent.mkdir(parents=True,exist_ok=True)
 tmp=target.with_name(target.name+'.combined-tmp');shutil.copy2(R/'product-device'/p,tmp);os.replace(tmp,target)
board=D/'BoardConfig.mk';text=board.read_text();assert text.count('TARGET_KERNEL_CONFIG := asus_p00a_defconfig')==1;text=text.replace('TARGET_KERNEL_CONFIG := asus_p00a_defconfig','TARGET_KERNEL_CONFIG := asus_p00a_combined_defconfig');board.write_text(text)
shutil.copy2(image,D/'prebuilt/Image.gz-dtb')
shutil.copy2(R/'product-device/radio/wificond.rc',A/'system/connectivity/wificond/wificond.rc')
for p,h in network['connectivity_after'].items():
 target=A/'packages/modules/Connectivity'/p;tmp=target.with_name(target.name+'.combined-tmp');shutil.copy2(R/'platform-connectivity'/p,tmp);assert sha(tmp)==h;os.replace(tmp,target)
assert 'soc/11230000.mmc' in (D/'rootdir/fstab.mt8163').read_text()
release_file=R/'artifacts/active-product-kernel.release';assert not release_file.exists();release_file.write_text(kernel_release+'\n')
record={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'prior_full_exit':(P/'logs/full-build-r5.exit-code').read_text().strip(),'source_patch_sha256':sha(patch),'source_changed_files':source['changes'],'generated_defconfig':{'path':str(defconfig),'sha256':sha(defconfig),'matches_compiled_config':True},'kernel_release':{'value':kernel_release,'path':str(release_file),'sha256':sha(release_file)},'product_after':manifest(D),'kernel_sha256':sha(D/'prebuilt/Image.gz-dtb'),'wificond_sha256':sha(A/'system/connectivity/wificond/wificond.rc'),'connectivity_before':network['connectivity_before'],'connectivity_after':network['connectivity_after'],'network_handoff_manifest_sha256':network['manifest_sha256'],'qualified_input_receipt_sha256':sha(R/'evidence/qualified-combined-inputs.json'),'installclean_repeated':False,'calibration_uploaded':False}
receipt.write_text(json.dumps(record,indent=2)+'\n');print('Integrated under full-product lock; start a new incremental revision')
