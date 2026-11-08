import os,resource,pathlib,subprocess,json,hashlib
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
resource.setrlimit(resource.RLIMIT_CPU,(60,60))
P=pathlib.Path; A=P('/srv/android/lineage24'); R=P('/srv/android/asus-userdata-block-labels-20261106');R.mkdir(exist_ok=False)
paths=['external/selinux/libselinux/src/android/android_platform.c','external/selinux/libselinux/src/label_file.c','system/core/init/devices.cpp','device/asus/p00a/sepolicy/vendor/file_contexts','device/asus/p00a/rootdir/fstab.mt8163','device/asus/p00a/rootdir/ueventd.rc','system/sepolicy/tools/checkfc.c','system/sepolicy/private/fsck.te']
out={}
for name in paths:
 p=A/name
 if not p.exists():out[name]={'absent':True};continue
 b=p.read_bytes(); assert len(b)<300000
 q=R/'inputs'/name;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(b)
 lines=b.decode().splitlines();selected=[]
 keys=['file_context','selabel','SELABEL','best_match','mmcblk0p26','userdata','by-name','symlink','sepolicy','allow fsck','fsck,','u:object_r:block_device']
 for i,line in enumerate(lines):
  if any(k in line for k in keys):selected.append({'line':i+1,'text':'\n'.join(lines[max(0,i-2):min(len(lines),i+4)])})
 out[name]={'sha256':hashlib.sha256(b).hexdigest(),'selected':selected,'unchanged':p.read_bytes()==b}
out['installed_contexts']=[str(p) for p in (A/'out/target/product/p00a').glob('**/etc/selinux/*file_contexts*')]
out['tools']=[str(p) for p in (A/'out/host/linux-x86/bin').glob('*') if p.name in ['checkfc','sepolicy-analyze','sepolicy-check','sesearch','checkpolicy','secilc']]
out['policies']=[str(p) for p in (A/'out/target/product/p00a').glob('**/*') if p.name in ['sepolicy','precompiled_sepolicy']]
out['system_tools']={n:subprocess.run(['sh','-c','command -v '+n],capture_output=True,text=True,timeout=5).stdout for n in ['gcc','sesearch','seinfo']}
print(json.dumps(out,indent=2))
