from pathlib import Path
import os,json,hashlib
R=Path('/srv/android/asus-final-image-startup-20261107');exec(compile((R/'source/cow.py').read_text(),'cow.py','exec'))
assert 'COW_PATCH_COMPLETE modified=2 added_observer=2' in (R/'run-patch/serial.log').read_text()
changes=[]
for source,target,expected in [('system/bin/sh','system/bin/actual-runtime-observer',b'u:object_r:shell_exec:s0\0'),('system/etc/init/apexd.rc','system/etc/init/actual-runtime-observer.rc',b'u:object_r:system_file:s0\0')]:
 _,src=inode(lookup(source));off,dst=inode(lookup(target));assert u16(src,128)==32 and u16(dst,128)==32 and expected in src[160:];C.write(off+160,src[160:]);changes.append(dict(path=target,label=expected.decode().strip('\0'),inode=lookup(target)))
os.fsync(C.fd)
rows=[]
for path,payload in [('system/vendor/etc/fstab.mt8163','vendor.fstab'),('system/vendor/etc/selinux/vendor_file_contexts','vendor.contexts'),('system/bin/actual-runtime-observer','observer'),('system/etc/init/actual-runtime-observer.rc','observer.rc')]:
 assert contents(lookup(path))==(I/payload).read_bytes();rows.append(describe(path))
for path in ['system/vendor/etc/fstab.mt8163','system/vendor/etc/selinux/vendor_file_contexts']:
 off,b=inode(lookup(path));base=os.pread(C.base,256,off);assert b[160:]==base[160:] and b[:4]==base[:4] and b[24:26]==base[24:26]
assert contents(lookup('system/etc/init/hw/init.rc'))==(I/'original-init.rc').read_bytes()
d=dict(passed=True,changes=rows,labels=changes,core_init_byte_identical=True,APEX_payloads_not_touched=True,base_opened_read_only=True,cow_bytes=(I/'system.qcow2').stat().st_size,scope='Two existing files + two observer files; ext4 mount/allocation/inode metadata side effects; no full block audit')
(E/'cow-verification.json').write_text(json.dumps(d,indent=2));os.close(C.fd);os.close(C.base);os.chmod(I/'system.qcow2',0o444);print(json.dumps(d,indent=2))
