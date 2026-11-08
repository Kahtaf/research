from pathlib import Path
import json,os,hashlib,struct,re
R=Path('/srv/android/asus-r9-linkerconfig-ownership-fix-20261106');os.environ['TMPDIR']=str(R/'tmp');old=Path('/srv/android/asus-r9-actual-early-runtime-20261106/source/cow_verify.py').read_text();s=old.split('# Exact existing genuine xattr storage')[0];s=s.replace("R=Path('/srv/android/asus-r9-actual-early-runtime-20261106');I=R/'inputs';E=R/'evidence'","R=Path('/srv/android/asus-r9-linkerconfig-ownership-fix-20261106');I=R/'inputs/runtime-r1';E=R/'evidence'");s=s.replace('/srv/android/asus-r9-postbuild-validation-r2/validation/system-partition.raw','/srv/android/asus-root-enabled-incremental-r1/host-r2/validation/system-partition.raw');exec(compile(s,'runtime-cow-parser','exec'))
assert 'COW_PATCH_COMPLETE modified=2 added=3' in (R/'run-patch-r1/serial.log').read_text()
fc=(R/'inputs/root-enabled-plat_file_contexts').read_text();matches=[]
for line in fc.splitlines():
 a=line.split()
 if a and not line.startswith('#') and len(a)>=2:
  try:
   if re.fullmatch(a[0],'/system/bin/linkerconfig'):matches.append(line)
  except re.error:pass
assert any(x.split()[-1]=='u:object_r:linkerconfig_exec:s0' for x in matches),matches
labels=[]
for path,label,copyfrom in [('system/bin/actual-runtime-observer',b'u:object_r:shell_exec:s0\0','system/bin/sh'),('system/etc/init/actual-runtime-observer.rc',b'u:object_r:system_file:s0\0','system/etc/init/apexd.rc'),('system/bin/linkerconfig',b'u:object_r:linkerconfig_exec:s0\0',None)]:
 off,ib=inode(lookup(path));assert u16(ib,128)==32;before=describe(path)
 if copyfrom:
  _,src=inode(lookup(copyfrom));body=src[160:];assert label in body
 else:
  body=bytearray(96);body[:4]=bytes.fromhex('000002ea');offs=96-4-((len(label)+3)//4*4);struct.pack_into('<BBHIII',body,4,7,6,offs,0,len(label),0);body[20:27]=b'selinux';body[4+offs:4+offs+len(label)]=label
 C.write(off+160,bytes(body));after=describe(path);assert label in bytes.fromhex(after['raw_inline_xattr_hex']);labels.append(dict(path=path,before=before,after=after,copyfrom=copyfrom))
os.fsync(C.fd);files=[]
for path,payload,mode,uid,gid in [('system/vendor/etc/fstab.mt8163','vendor.fstab',0o100644,0,0),('system/etc/init/hw/init.rc','init.rc',0o100644,0,0),('system/bin/linkerconfig','candidate',0o100755,0,2000),('system/bin/actual-runtime-observer','observer',0o100755,0,2000),('system/etc/init/actual-runtime-observer.rc','observer.rc',0o100644,0,0)]:
 d=describe(path);assert contents(lookup(path))==(I/payload).read_bytes();assert d['mode']==oct(mode) and d['uid']==uid and d['gid']==gid;files.append(d)
 if path in ['system/vendor/etc/fstab.mt8163','system/etc/init/hw/init.rc']:
  off,b=inode(lookup(path));base=os.pread(C.base,256,off);assert b[160:]==base[160:] and b[:4]==base[:4] and b[24:26]==base[24:26] and b[8:12]==base[8:12] and b[16:20]==base[16:20]
(E/'runtime-cow-verification.json').write_text(json.dumps(dict(passed=True,files=files,label_changes=labels,candidate_file_context_matches=matches,original_xattrs_modes_ownership_atime_mtime_preserved=True,cow_bytes=(I/'system.qcow2').stat().st_size,cow_sha256=hashlib.sha256((I/'system.qcow2').read_bytes()).hexdigest()),indent=2));os.chmod(I/'system.qcow2',0o444);print(json.dumps({'passed':True,'cow_bytes':(I/'system.qcow2').stat().st_size,'candidate_file_context_matches':matches},indent=2))
