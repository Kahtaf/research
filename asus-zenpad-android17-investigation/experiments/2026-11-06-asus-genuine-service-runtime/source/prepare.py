from pathlib import Path
import shutil,hashlib,json,subprocess,os
R=Path('/srv/android/asus-genuine-service-runtime');P=Path('/srv/android/asus-firstboot-runtime');T=Path('/srv/android/lineage24');I=R/'inputs/boot-r1';I.mkdir()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
# Qualified virtual kernel and prior genuine enforcing input, copied read-only.
shutil.copytree(P/'inputs/boot-r10',I,dirs_exist_ok=True,symlinks=True)
K=R/'inputs/kernel-r7';K.mkdir()
for src,dst,h in [(P/'kernel-build-r7/arch/arm64/boot/Image',K/'Image','95a62a8bccd3085d682a89b6c74c7afd0961cebd1e3137b256229849920b549b'),(P/'kernel-build-r7/.config',K/'config','c2ea1277e1574da39d1d55d31bde7bda439ab624561ad3c6a6f4730e38f57834')]:
 assert sha(src)==h;shutil.copy2(src,dst);assert sha(dst)==h
C=R/'inputs/capture-r1/out/target/product/p00a';root=I/'root';changes=[]
for src in (C/'system').rglob('*'):
 if not src.is_file():continue
 rel=src.relative_to(C);dst=root/rel
 # Preserve coherent compiled policy/contexts from prior input pending explicit comparison.
 if 'selinux' in rel.parts:continue
 before=sha(dst) if dst.is_file() else None
 dst.parent.mkdir(parents=True,exist_ok=True)
 if dst.is_symlink():dst.unlink()
 shutil.copy2(src,dst);changes.append(dict(path=str(rel),before=before,after=sha(dst)))
# Exact previous completed linkerconfig input, preserved provenance.
shutil.copy2(P/'inputs/late-outputs-r1/linkerconfig',root/'system/bin/linkerconfig');(root/'system/bin/linkerconfig').chmod(0o755)
# Current selected generated init, no instrumentation diff in core init.rc.
src=T/'out/soong/.intermediates/system/core/rootdir/init.rc/android_arm64_armv8-a/init.rc'
init_rc_hash=sha(src);shutil.copy2(src,root/'system/etc/init/hw/init.rc');assert init_rc_hash==sha(src)
# Keep the separate observer service/triggers from prior input, no readiness writes.
# Own the inherited host labeling tools and first-stage binary too.
shutil.copy2(P/'inputs/early-r1/init_first_stage',I/'init_first_stage')
shutil.copy2(P/'source/seed_exec.c',R/'source/seed_exec.c')
# Completed genuine ICU implementation needed by current libsqlite. This system variant
# has its own real DT_NEEDED closure, copied without substituting any symbol provider.
B=T/'out/soong/.intermediates';names={}
for p in B.rglob('*.so'):
 if p.parent.name in ('android_arm64_armv8-a_shared','android_arm64_armv8-a_shared_current','android_arm64_armv8-a_shared_cfi'):names.setdefault(p.name,[]).append(p)
queue=[root/'system/lib64/libsqlite.so'];seen=set();extra=[]
import re
while queue:
 p=queue.pop()
 for n in re.findall(r'\(NEEDED\).*\[(.*?)\]',subprocess.check_output(['readelf','-d',str(p)],text=True)):
  if n in seen:continue
  seen.add(n);dest=root/'system/lib64'/n
  if not dest.is_file():
   candidates=names.get(n,[]);assert len(candidates)==1,(n,candidates)
   src=candidates[0];a=sha(src);shutil.copy2(src,dest);assert sha(src)==a==sha(dest);extra.append(dict(source=str(src),destination=str(dest),sha256=a))
  queue.append(dest)
# Freeze current source/copy manifest, policy and selected config provenance.
(R/'evidence/preparation-r1.json').write_text(json.dumps(dict(kernel_image=sha(K/'Image'),kernel_config=sha(K/'config'),current_init_rc=init_rc_hash,overlay=changes,extra_dependencies=extra,policy=sha(root/'system/vendor/etc/selinux/precompiled_sepolicy'),fixture_adaptation='Inherited vda=data, vdb=system mapping; generated current core init.rc; prior separate observation service; no physical USB/network'),indent=2))
print('prepared',len(changes),'overlay files',len(extra),'extra libraries')
