from pathlib import Path
import subprocess,base64
from remote import BASE
L=Path(__file__).resolve().parents[1];P=L.parent/'2026-11-06-asus-r9-linkerconfig-ownership-fix';old='/srv/android/asus-r9-linkerconfig-ownership-fix-20261106';new='/srv/android/asus-odsign-startup-20261106';files={}
x=(P/'source/verify_runtime_r3_cow.py').read_text().replace(old,new).replace('runtime-r3','runtime-r1').replace('run-patch-r3','run-patch-r1');files['verify_runtime_cow.py']=x
x=(P/'source/audit_runtime_cow.py').read_text().replace(old,new).replace('runtime-r1','runtime-r1')
a=x.index('allowedpaths=');b=x.index(';allowedinos=',a)
x=x[:a]+"allowedpaths=['system/vendor/etc/fstab.mt8163','system/etc/init/hw/init.rc','system/vendor/etc/selinux/vendor_file_contexts','system/bin/actual-runtime-observer','system/etc/init/actual-runtime-observer.rc','system/bin','system/etc','system/etc/init','system/etc/actual-runtime-bin']+['system/etc/actual-runtime-bin/'+n for n in ['linkerconfig','linker','linker64','crash_dump32','crash_dump64','linker_asan','linker_asan64','linker_hwasan64']]"+x[b:];x=x.replace('off,ib=inode(n)\n for', 'off,ib=inode(n)\n if u16(ib,0)&0o170000 == 0o120000:continue\n for');files['audit_runtime_cow.py']=x
for n,v in files.items():(L/'source'/n).write_text(v)
code="from pathlib import Path\nR=Path('"+new+"')\nfiles="+repr(files)+"\nfor n,v in files.items():(R/'source'/n).write_text(v)\nexec(compile((R/'source/verify_runtime_cow.py').read_text(),'verify','exec'))\nexec(compile((R/'source/audit_runtime_cow.py').read_text(),'audit','exec'))\n"
raise SystemExit(subprocess.run(BASE+['python3 -'],input=code.encode()).returncode)
