from pathlib import Path
import subprocess,json,os,hashlib
R=Path('/srv/android/asus-r9-actual-early-runtime-20261106');G=Path('/srv/android/asus-genuine-service-runtime');d={}
for n in ['evidence/observer-compile.json','inputs/boot-r9/root/system/etc/init/hw/init.rc','source/observer.c']:
 p=G/n;d[n]=p.read_text()
for cmd in [['which','qemu-system-aarch64'],['ls','-l','/dev/fuse']]:
 p=subprocess.run(cmd,capture_output=True,text=True);d[str(cmd)]=dict(rc=p.returncode,stdout=p.stdout,stderr=p.stderr)
D=Path('/srv/android/asus-full-system-observer-preparation-20261106/immutable/bin/debugfs');env=os.environ.copy();env['LD_LIBRARY_PATH']=str(D.parents[1]/'lib64')
for cmd in ['cat system/vendor/etc/fstab.mt8163','cat system/etc/init/hw/init.rc','ls -l system/etc/init','cat system/vendor/etc/selinux/vendor_file_contexts','stat system/vendor/etc/fstab.mt8163','ea_list system/vendor/etc/fstab.mt8163','stat system/bin/sh','ea_list system/bin/sh','stat system/etc/init/apexd.rc','ea_list system/etc/init/apexd.rc']:
 p=subprocess.run([str(D),'-R',cmd,'/srv/android/asus-r9-postbuild-validation-r2/validation/system-partition.raw'],capture_output=True,text=True,env=env,timeout=10);d[cmd]=dict(stdout=p.stdout,stderr=p.stderr)
(R/'evidence/inspection2.json').write_text(json.dumps(d,indent=2));print(json.dumps({k:v for k,v in d.items() if k not in ['cat system/vendor/etc/selinux/vendor_file_contexts','ls -l system/etc/init','source/observer.c']},indent=2))
