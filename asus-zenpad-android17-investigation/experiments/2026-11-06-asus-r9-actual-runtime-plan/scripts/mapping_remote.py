import os,pathlib,json,subprocess,resource,signal,hashlib
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(60,60));signal.alarm(90)
P=pathlib.Path;D=P('/srv/android/asus-full-system-observer-preparation-20261106/immutable/bin/debugfs');raw='/srv/android/asus-r9-postbuild-validation-r2/validation/system-partition.raw';env=os.environ.copy();env['LD_LIBRARY_PATH']=str(D.parents[1]/'lib64');d={'raw':{},'installed_small_paths':{},'old_observer':{}}
for cmd in ['ls -l /','cat fstab.mt8163','cat init.mt8163.rc','cat system/vendor/etc/init/hw/init.mt8163.rc','cat system/vendor/etc/fstab.mt8163','ls -l system/etc/security/apex','stat system/etc/security/apexkeys.txt','stat system/etc/apexkeys.txt','cat system/etc/init/apexd.rc','cat system/etc/init/hw/init.boringssl.zygote64_32.rc']:
 p=subprocess.run([str(D),'-R',cmd,raw],stdin=subprocess.DEVNULL,capture_output=True,text=True,timeout=10,env=env);assert len(p.stdout)+len(p.stderr)<100000;d['raw'][cmd]=dict(exit=p.returncode,stdout=p.stdout,stderr=p.stderr)
A=P('/srv/android/lineage24/out/target/product/p00a')
for rel in ['apexkeys.txt','system/etc/security/apexkeys.txt','system/etc/apexkeys.txt','system/etc/security/apex/com.android.runtime.avbpubkey','system/vendor/etc/fstab.mt8163']:
 p=A/rel;r=dict(path=str(p),exists=p.exists(),symlink=p.is_symlink())
 if p.is_file():r['bytes']=p.stat().st_size;r['sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
 d['installed_small_paths'][rel]=r
root=P('/srv/android/asus-genuine-service-runtime/inputs/boot-r9/root')
for rel in ['init.mt8163.rc','fstab.mt8163','system/vendor/etc/fstab.mt8163','system/etc/init/firstboot-observer.rc','system/etc/init/hw/firstboot-observer.rc','system/vendor/etc/init/hw/init.mt8163.rc']:
 p=root/rel
 if p.is_file():d['old_observer'][rel]=p.read_text()
print(json.dumps(d,indent=2))
