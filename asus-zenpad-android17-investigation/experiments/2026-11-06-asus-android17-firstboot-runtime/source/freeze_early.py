from pathlib import Path
import hashlib,json,subprocess as s,re,shutil
R=Path('/srv/android/asus-firstboot-runtime');I=R/'inputs/early-r1';I.mkdir()
T=Path('/srv/android/lineage24'); B=T/'out/soong/.intermediates'; P=Path('/srv/android/asus-android17-runtime-prereqs'); manifest=[]
def freeze(src,dest,expect=None):
 src=Path(src); a=src.stat();d=src.read_bytes();b=src.stat();h=hashlib.sha256(d).hexdigest()
 assert (a.st_ino,a.st_size,a.st_mtime_ns)==(b.st_ino,b.st_size,b.st_mtime_ns) and hashlib.sha256(src.read_bytes()).hexdigest()==h
 if expect: assert h==expect
 target=I/dest;target.parent.mkdir(parents=True,exist_ok=True);assert not target.exists();target.write_bytes(d)
 manifest.append(dict(source=str(src),path=dest,bytes=len(d),sha256=h));return target
freeze(P/'build-r4/arch/arm64/boot/Image','Image','113c4f19c736b949626c62bbf68cf23c9e3c5a821ec6ab031a5684cdcba14431')
freeze(P/'build-r4/.config','kernel.config')
freeze(B/'system/sepolicy/precompiled_sepolicy/android_common/p00a/precompiled_sepolicy','root/policy')
freeze(B/'system/core/init/init_first_stage/android_ramdisk_arm64_armv8-a/init','init_first_stage')
freeze(B/'system/core/init/init_second_stage/android_arm64_armv8-a/init','root/system/bin/init')
for f in (P/'inputs/root').rglob('*'):
 if f.is_file(): freeze(f,'root/'+str(f.relative_to(P/'inputs/root')))
names={}
for p in B.rglob('*.so'):
 if p.parent.name in ('android_arm64_armv8-a_shared','android_arm64_armv8-a_shared_cfi'): names.setdefault(p.name,[]).append(p)
queue=[I/'root/system/bin/init'];seen=set()
while queue:
 f=queue.pop();dyn=s.check_output(['readelf','-d',str(f)],text=True)
 for name in re.findall(r'Shared library: \[(.*?)\]',dyn):
  if name in seen or name=='ld-android.so':continue
  seen.add(name);dest=I/'root/system/lib64'/name
  if not dest.exists():
   c=names.get(name,[]);assert len(c)==1,(name,c);freeze(c[0],'root/system/lib64/'+name)
  queue.append(dest)
for f in (B/'system/sepolicy').rglob('*'):
 if f.is_file() and (f.suffix in ('.cil','.conf','.sha256') or f.name=='precompiled_sepolicy'):
  freeze(f,'compiled-policy/'+str(f.relative_to(B/'system/sepolicy')))
for root in ['device/asus/p00a/rootdir','device/asus/p00a/sepolicy','device/asus/p00a/firstboot','system/core/rootdir']:
 for f in (T/root).rglob('*'):
  if f.is_file() and '.git' not in f.parts:freeze(f,'source/'+str(f.relative_to(T)))
for f in ['system/core/init/selinux.cpp','system/core/init/first_stage_init.cpp','system/core/init/init.cpp','system/core/init/property_service.cpp','system/core/init/apex_init_util.cpp','device/asus/p00a/BoardConfig.mk','device/asus/p00a/device.mk']:
 freeze(T/f,'source/'+f)
(R/'evidence/early-input-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('frozen',len(manifest),'files')
