from pathlib import Path
import hashlib,json,shutil,tarfile,os,datetime
R=Path('/srv/android/asus-firstboot-runtime');D=R/'handoff-r2';assert not D.exists();D.mkdir()
def copy(src,rel):
 src=Path(src);dst=D/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
for f in (R/'source').rglob('*'):
 if f.is_file() and f.suffix in ['.py','.c','.patch']:copy(f,Path('source')/f.relative_to(R/'source'))
for f in (R/'stagedpatches').rglob('*'):
 if f.is_file():copy(f,Path('stagedpatches')/f.relative_to(R/'stagedpatches'))
for f in (R/'evidence').iterdir():
 if f.is_file() and f.suffix in ['.json','.txt','.log','.d']:copy(f,Path('evidence')/f.name)
for run in sorted(R.glob('run-*')):
 if not run.is_dir():continue
 for f in run.iterdir():
  if f.is_file() and f.suffix in ['.json','.log','.py','.c']:copy(f,Path('evidence')/run.name/f.name)
for sub in ['api-generators-r1','api-generators-r2','apexkeys-generator-r1','apexkeys-generator-r2','service-rules-r2','missing-api-rules-r1','property-generator-r2']:
 base=R/'inputs'/sub
 for f in base.iterdir():
  if f.is_file() and f.suffix in ['.json','.txt','.ninja','.textproto','.py','.ninja-command']:copy(f,Path('inputs')/sub/f.name)
 for child in ['manifests','outputs']:
  if not (base/child).exists():continue
  for f in (base/child).rglob('*'):
   if f.is_file():copy(f,Path('inputs')/sub/f.relative_to(base))
copy(R/'inputs/property-generator-r2/mirror/out/target/product/p00a/system/vendor/build.prop','generated/vendor-build.prop')
copy(R/'inputs/apexkeys-generator-r2/mirror/out/target/product/p00a/obj/PACKAGING/apexkeys_intermediates/apexkeys.txt','generated/apexkeys.txt')
for n in ['r5','r6','r7']:copy(R/f'kernel-build-{n}/.config',f'kernel/kernel-{n}.config')
copy(R/'kernel-build-r7/arch/arm64/boot/Image','kernel/Image')
for rel in ['include/linux/cgroup-defs.h','kernel/cgroup.c','kernel/cpuset.c']:copy(R/'kernel-cpuset-r1'/rel,Path('tested-source')/rel)
copy(R/'stagedpatches/blkio/after.defconfig','tested-source/arch/arm64/configs/asus_p00a_defconfig')
root=R/'inputs/boot-r10/root';tree=[]
for p in sorted(root.rglob('*')):
 if p.is_symlink():tree.append(dict(path=str(p.relative_to(root)),kind='symlink',target=os.readlink(p)))
 elif p.is_file():tree.append(dict(path=str(p.relative_to(root)),kind='file',bytes=p.stat().st_size,mode=oct(p.stat().st_mode&0o7777),sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
(D/'evidence/boot-input-tree.json').write_text(json.dumps(tree,indent=2))
for src,rel in [('system/etc/cgroups.json','cgroups.json'),('system/vendor/etc/selinux/precompiled_sepolicy','precompiled_sepolicy'),('system/etc/init/hw/init.rc','fixture-init.rc'),('system/etc/init/firstboot-observe.rc','firstboot-observe.rc')]:copy(root/src,Path('input-identity')/rel)
copy(R/'inputs/early-r1/init_first_stage','input-identity/init_first_stage')
for rel in ['system/bin/init','system/bin/ueventd','system/bin/firstboot-observer']:
 p=root/rel
 if p.is_file():copy(p,Path('input-identity')/Path(rel).name)
copy(R/'report.md','report.md')
manifest=[]
for f in sorted(D.rglob('*')):
 if f.is_file():manifest.append(dict(path=str(f.relative_to(D)),bytes=f.stat().st_size,sha256=hashlib.sha256(f.read_bytes()).hexdigest()))
(D/'manifest.json').write_text(json.dumps(dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='Targeted firstboot kernel/init/SELinux/cgroups/property qualification; crypto/APEX/authenticated-adbd pending genuine build outputs',entries=manifest),indent=2));archive=R/'artifacts/capture-r2.tar.gz';assert not archive.exists()
with tarfile.open(archive,'w:gz') as tar:tar.add(D,arcname='handoff-r2')
print(json.dumps(dict(path=str(archive),sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),manifest_sha256=hashlib.sha256((D/'manifest.json').read_bytes()).hexdigest(),entries=len(manifest),bytes=archive.stat().st_size),indent=2))
