from pathlib import Path
import os,json,hashlib,stat
R=Path('/srv/android/asus-r9-linkerconfig-ownership-fix-20261106');os.environ['TMPDIR']=str(R/'tmp');script=(R/'source/actual_metadata.py').read_text() if (R/'source/actual_metadata.py').exists() else None
# The frozen public reader script is uploaded alongside this admission.
exec(compile(script.split("D={'raw_identity_before'")[0],'readonly-ext4-reader','exec'))
D=json.loads((R/'evidence/actual-metadata.json').read_text());paths=[x for x,row in D['filesystem_files'].items() if row.get('exists') is not False and not x.endswith('.prop')]+[r['package_path'] for r in D['packages']]+['system/bin/init','system/etc/init/hw/init.rc','system/vendor/etc/fstab.mt8163','system/vendor/etc/selinux/precompiled_sepolicy'];old={}
for path in paths:
 b=get(path);old[path]={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
os.close(fd);raw=Path('/srv/android/asus-root-enabled-incremental-r1/host-r2/validation/system-partition.raw');st=raw.stat();newidentity={'path':str(raw),'dev':st.st_dev,'inode':st.st_ino,'bytes':st.st_size,'mtime_ns':st.st_mtime_ns,'ctime_ns':st.st_ctime_ns,'mode':oct(stat.S_IMODE(st.st_mode))};assert st.st_size==3753902080 and stat.S_IMODE(st.st_mode)==0o444;fd=os.open(raw,os.O_RDONLY|os.O_NOFOLLOW);cache={};sb=pread(1024,1024);assert 1024<<u32(sb,24)==bs and u32(sb,40)==ipg and u16(sb,88)==isz
for path,row in old.items():b=get(path);assert len(b)==row['bytes'] and hashlib.sha256(b).hexdigest()==row['sha256'],path
props={};pub={}
for path in ['system/build.prop','system/system_ext/etc/build.prop','system/product/etc/build.prop']:
 try:b=get(path)
 except KeyError:continue
 pub[path]={'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
 for line in b.decode().splitlines():
  if line.startswith(('ro.debuggable=','ro.secure=','ro.adb.secure=')):
   k,v=line.split('=',1);props.setdefault(k,[]).append({'path':path,'value':v})
assert {x['value'] for x in props['ro.debuggable']}=={'1'} and {x['value'] for x in props['ro.secure']}=={'1'} and {x['value'] for x in props['ro.adb.secure']}=={'1'}
boot=Path('/srv/android/asus-root-enabled-incremental-r1/host-r2/validation/UNTESTED-sdk37-combined-boot.img');b=boot.read_bytes();assert len(b)==9242624 and hashlib.sha256(b).hexdigest()=='784d4dc565e7742ea607683d2a67d1fdb066764bddfa369895cbaaf6f048b435'
for name,path in [('init.rc','system/etc/init/hw/init.rc'),('vendor.fstab','system/vendor/etc/fstab.mt8163'),('plat_file_contexts','system/etc/selinux/plat_file_contexts')]: (R/'inputs'/('root-enabled-'+name)).write_bytes(get(path))
st=raw.stat();after={'path':str(raw),'dev':st.st_dev,'inode':st.st_ino,'bytes':st.st_size,'mtime_ns':st.st_mtime_ns,'ctime_ns':st.st_ctime_ns,'mode':oct(stat.S_IMODE(st.st_mode))};assert after==newidentity
result=dict(raw_identity=newidentity,raw_sha256_parent_admitted='04b4d81f486ce4a17609300c3f6d2f92cecc1938ee0f0e64019a29bd8c870785',no_new_fullraw_hash=True,properties=props,property_file_pins=pub,unchanged_metadata_and_packages=old,boot={'path':str(boot),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()},raw_identity_unchanged=True,all39_apex_packages_and_all_linker_provider_metadata_byte_identical_to_frozen_run1=True,source_MK_parent_admitted='9eef1d1e5463f43500863604641f8fb3af8d91fb9100b83f231b216041f79c75')
(R/'evidence/root-enabled-admission.json').write_text(json.dumps(result,indent=2));print(json.dumps({'new_raw_identity':newidentity,'properties':props,'unchanged_files_and_packages':len(old)},indent=2))
