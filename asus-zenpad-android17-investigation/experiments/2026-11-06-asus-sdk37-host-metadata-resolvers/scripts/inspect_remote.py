import os,resource,signal,pathlib,json,hashlib,subprocess
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(60,60));signal.alarm(90)
P=pathlib.Path;R=P('/srv/android/asus-sdk37-host-metadata-resolvers-20261106');R.mkdir();A=P('/srv/android/lineage24');d={'remote_root':str(R),'sources':{},'libraries':{}}
paths=['system/core/libcutils/include/private/fs_config.h','system/core/libcutils/include/private/android_filesystem_config.h','system/core/libcutils/fs_config.cpp','system/core/libcutils/fs_config.h','system/core/libcutils/Android.bp','external/selinux/libselinux/Android.bp','external/selinux/libselinux/include/selinux/label.h','external/selinux/libselinux/include/selinux/selinux.h','external/selinux/libselinux/src/label_file.c','external/selinux/libselinux/src/label_file.h','external/selinux/libselinux/src/label.c']
for name in paths:
 p=A/name
 if p.exists():
  b=p.read_bytes();d['sources'][name]={'sha256':hashlib.sha256(b).hexdigest(),'text':b.decode(errors='replace')}
 else:d['sources'][name]={'missing':True}
libnames=['out/host/linux-x86/lib64/libcutils.so','out/host/linux-x86/lib64/libselinux.so','out/host/linux-x86/lib64/libbase.so','out/host/linux-x86/lib64/libpcre2.so','out/host/linux-x86/lib64/libpcre2-8.so','out/host/linux-x86/bin/sefcontext_compile','out/soong/.intermediates/external/selinux/libselinux/libselinux/linux_glibc_x86_64_static/libselinux.a','out/soong/.intermediates/external/selinux/libselinux/libselinux/linux_glibc_x86_64_shared/libselinux.so']
for name in libnames:
 p=A/name;item={'exists':p.is_file()};d['libraries'][name]=item
 if p.is_file():
  item.update(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
  if p.suffix=='.so' or name.endswith('sefcontext_compile'):
   item['ldd']=subprocess.run(['/usr/bin/ldd',str(p)],capture_output=True,text=True,timeout=15).stdout
   if p.suffix=='.so':
    item['selected_symbols']=subprocess.run(['/usr/bin/nm','-D','--defined-only',str(p)],capture_output=True,text=True,timeout=15).stdout
    item['selected_symbols']='\n'.join(l for l in item['selected_symbols'].splitlines()if any(s in l for s in ['fs_config','selabel_','freecon']))
(R/'inspection.json').write_text(json.dumps(d,indent=2));print(json.dumps(d,indent=2))
