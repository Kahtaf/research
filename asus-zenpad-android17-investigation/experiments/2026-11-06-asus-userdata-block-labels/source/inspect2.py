import os,resource,pathlib,subprocess,json,hashlib
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(60,60))
P=pathlib.Path;A=P('/srv/android/lineage24');R=P('/srv/android/asus-userdata-block-labels-20261106')
names=['external/selinux/libselinux/src/android/android.c','system/core/init/selabel.cpp','system/core/init/devices.cpp','system/sepolicy/tools/sepolicy-check.c','device/asus/p00a/sepolicy/vendor/file_contexts','device/asus/p00a/rootdir/ueventd.rc']
out={}
for name in names:
 p=A/name
 if not p.exists():continue
 b=p.read_bytes();q=R/'inputs'/name;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(b)
 lines=b.decode().splitlines();ranges=[]
 if name.endswith('android.c'):
  ranges=[(i-4,i+22) for i,l in enumerate(lines) if 'file_context' in l or 'selinux_android_file_context_handle' in l]
 elif name.endswith('devices.cpp'):ranges=[(90,170),(540,620)]
 elif name.endswith('selabel.cpp') or name.endswith('sepolicy-check.c'):ranges=[(0,len(lines))]
 else:ranges=[(0,len(lines))]
 out[name]={'sha256':hashlib.sha256(b).hexdigest(),'text':'\n'.join(f'{i+1}: {lines[i]}' for i in sorted(set(i for s,e in ranges for i in range(max(0,s),min(e,len(lines)))))),'unchanged':p.read_bytes()==b}
for n in ['checkfc','sepolicy-analyze']:
 r=subprocess.run([str(A/'out/host/linux-x86/bin'/n),'--help'],capture_output=True,text=True,timeout=10);out[n]={'out':r.stdout,'err':r.stderr,'exit':r.returncode}
out['sepol_services']=(A/'external/selinux/libsepol/include/sepol/policydb/services.h').read_text()
print(json.dumps(out,indent=2))
