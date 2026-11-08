from pathlib import Path
import json,os,hashlib,struct,re
R=Path('/srv/android/asus-r9-linkerconfig-ownership-fix-20261106');os.environ['TMPDIR']=str(R/'tmp');old=Path('/srv/android/asus-r9-actual-early-runtime-20261106/source/cow_verify.py').read_text();s=old.split('# Exact existing genuine xattr storage')[0].replace("R=Path('/srv/android/asus-r9-actual-early-runtime-20261106');I=R/'inputs';E=R/'evidence'","R=Path('/srv/android/asus-r9-linkerconfig-ownership-fix-20261106');I=R/'inputs/runtime-r3';E=R/'evidence'").replace('/srv/android/asus-r9-postbuild-validation-r2/validation/system-partition.raw','/srv/android/asus-root-enabled-incremental-r1/host-r2/validation/system-partition.raw');exec(compile(s,'r2-cow-parser','exec'));assert 'COW_PATCH_COMPLETE modified=3 added_bin_directory=1' in (R/'run-patch-r3/serial.log').read_text();newlabels={'system/bin/actual-runtime-observer':'shell_exec','system/etc/init/actual-runtime-observer.rc':'system_file','system/etc/actual-runtime-bin':'system_file'}
for n,t in [('linker','system_linker_exec'),('linker64','system_linker_exec'),('linkerconfig','linkerconfig_exec'),('crash_dump32','crash_dump_exec'),('crash_dump64','crash_dump_exec'),('linker_asan','system_file'),('linker_asan64','system_file'),('linker_hwasan64','system_file')]:newlabels['system/etc/actual-runtime-bin/'+n]=t
for path,typ in newlabels.items():
 off,ib=inode(lookup(path));assert u16(ib,128)==32;label=('u:object_r:'+typ+':s0\0').encode();body=bytearray(96);body[:4]=bytes.fromhex('000002ea');voff=96-4-((len(label)+3)//4*4);struct.pack_into('<BBHIII',body,4,7,6,voff,0,len(label),0);body[20:27]=b'selinux';body[4+voff:4+voff+len(label)]=label;C.write(off+160,body)
 if path.startswith('system/etc/actual-runtime-bin'):
  # Original runtime bin has epoch-zero metadata and 0755, including symlinks.
  C.write(off+8,b'\0'*12);C.write(off+132,b'\0'*20)
  if path.rsplit('/',1)[-1] in ['linker_asan','linker_asan64','linker_hwasan64']:C.write(off,struct.pack('<H',0o120755))
os.fsync(C.fd);rows=[]
for path,payload in [('system/vendor/etc/fstab.mt8163','vendor.fstab'),('system/etc/init/hw/init.rc','init.rc'),('system/vendor/etc/selinux/vendor_file_contexts','vendor.contexts'),('system/bin/actual-runtime-observer','observer'),('system/etc/init/actual-runtime-observer.rc','observer.rc')]:
 assert contents(lookup(path))==(I/payload).read_bytes();d=describe(path);rows.append(d)
 if path in ['system/vendor/etc/fstab.mt8163','system/etc/init/hw/init.rc','system/vendor/etc/selinux/vendor_file_contexts']:
  off,b=inode(lookup(path));base=os.pread(C.base,256,off);assert b[160:]==base[160:] and b[:4]==base[:4] and b[24:26]==base[24:26] and b[8:12]==base[8:12] and b[16:20]==base[16:20]
meta=json.loads((E/'runtime-bin-preserved.json').read_text());binrows=[]
for n,row in meta.items():
 path='system/etc/actual-runtime-bin/'+n;off,ib=inode(lookup(path));assert u16(ib,2)==0 and u16(ib,24)==2000
 if 'symlink' in row:
  assert u16(ib,0)==0o120755;target=ib[40:40+u32(ib,4)].decode();assert target==row['symlink'];binrows.append(dict(path=path,symlink=target,uid=0,gid=2000,mode='0120755',label=newlabels[path]))
 else:
  b=contents(lookup(path));expected=(I/'candidate').read_bytes() if n=='linkerconfig' else (R/'inputs/runtime-bin-preserved'/n).read_bytes();assert b==expected;d=describe(path);assert d['mode']=='0o100755';binrows.append(d)
# Explicit fixture-only mapping; parent source metadata deltas are not pulled into this image.
base=(R/'inputs/root-enabled-vendor.contexts').read_bytes();assert contents(lookup('system/vendor/etc/selinux/vendor_file_contexts'))==base+b'\n/dev/block/vda    u:object_r:userdata_block_device:s0\n'
result=dict(passed=True,modified_file_metadata=rows,preserved_runtime_bin=binrows,new_labels=newlabels,compiled_policy_unchanged=True,APEX_package_unchanged=True,only_changed_runtime_bin_payload='linkerconfig',cow_bytes=(I/'system.qcow2').stat().st_size,cow_sha256=hashlib.sha256((I/'system.qcow2').read_bytes()).hexdigest());(E/'runtime-r3-cow-verification.json').write_text(json.dumps(result,indent=2));os.chmod(I/'system.qcow2',0o444);print(json.dumps({'passed':True,'cow_bytes':result['cow_bytes'],'bin_entries':len(binrows)},indent=2))
