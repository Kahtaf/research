from pathlib import Path
import os,json,subprocess as sp,zipfile,io,shutil,re,hashlib
R=Path('/srv/android/asus-r9-linkerconfig-ownership-fix-20261106');os.environ['TMPDIR']=str(R/'tmp');os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
# Re-extract only the small unchanged runtime bin directory, preserving symlink identities.
defs=(R/'source/actual_metadata.py').read_text().split("D={'raw_identity_before'")[0];exec(compile(defs,'readonly-original-runtime','exec'));b=get('system/apex/com.android.runtime.apex');z=zipfile.ZipFile(io.BytesIO(b));payload=R/'tmp/runtime-r2-payload.img';payload.write_bytes(z.read('apex_payload.img'));extract=R/'tmp/runtime-r2-extract';tool=R/'inputs/host-deps/root/usr/bin/fsck.erofs';q=sp.run([str(tool),'--extract='+str(extract),'--no-preserve',str(payload)],capture_output=True,text=True,timeout=20);assert q.returncode==0,q.stderr;bins=R/'inputs/runtime-bin-preserved';bins.mkdir();meta={}
for f in sorted((extract/'bin').iterdir()):
 d=bins/f.name
 if f.is_symlink():d.symlink_to(os.readlink(f));meta[f.name]={'symlink':os.readlink(f),'uid':0,'gid':2000,'mode':'0120755'}
 else:shutil.copyfile(f,d);meta[f.name]={'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'uid':0,'gid':2000,'mode':'0100755'}
assert set(meta)=={'crash_dump32','crash_dump64','linker','linker64','linker_asan','linker_asan64','linker_hwasan64','linkerconfig'};(R/'evidence/runtime-bin-preserved.json').write_text(json.dumps(meta,indent=2));shutil.rmtree(extract);payload.unlink()
# Preserve all r1 code before fixture-only corrections.
for n in ['runtime_observer.c','runtime_patcher.c']:
 p=R/'source'/n
 if p.exists():shutil.copyfile(p,R/'source'/('r1-'+n))
patcher=(R/'source/runtime_patcher.c').read_text();patcher=patcher.replace('put("/candidate","/mnt/system/bin/linkerconfig",0,0755,2000);','''put("/vendor.contexts","/mnt/system/vendor/etc/selinux/vendor_file_contexts",1,0,0);
if(mkdir("/mnt/system/etc/actual-runtime-bin",0755)||chown("/mnt/system/etc/actual-runtime-bin",0,2000))die("bin dir");
put("/runtime-bin/linkerconfig","/mnt/system/etc/actual-runtime-bin/linkerconfig",0,0755,2000);
put("/runtime-bin/linker","/mnt/system/etc/actual-runtime-bin/linker",0,0755,2000);
put("/runtime-bin/linker64","/mnt/system/etc/actual-runtime-bin/linker64",0,0755,2000);
put("/runtime-bin/crash_dump32","/mnt/system/etc/actual-runtime-bin/crash_dump32",0,0755,2000);
put("/runtime-bin/crash_dump64","/mnt/system/etc/actual-runtime-bin/crash_dump64",0,0755,2000);
if(symlink("linker","/mnt/system/etc/actual-runtime-bin/linker_asan")||symlink("linker64","/mnt/system/etc/actual-runtime-bin/linker_asan64")||symlink("linker64","/mnt/system/etc/actual-runtime-bin/linker_hwasan64"))die("symlinks");
if(lchown("/mnt/system/etc/actual-runtime-bin/linker_asan",0,2000)||lchown("/mnt/system/etc/actual-runtime-bin/linker_asan64",0,2000)||lchown("/mnt/system/etc/actual-runtime-bin/linker_hwasan64",0,2000))die("symlink owner");''').replace('COW_PATCH_COMPLETE modified=2 added=3','COW_PATCH_COMPLETE modified=3 added_bin_directory=1');(R/'source/runtime_patcher_r2.c').write_text(patcher)
# Derive new fresh preparation; never reuse r1 COW, DATA, or entropy.
src=(R/'source/prepare_runtime.py').read_text().replace("runtime-r1","runtime-r2").replace("E/'runtime-prepare-commands.json'","E/'runtime-r2-prepare-commands.json'").replace("E/'runtime-adaptations.json'","E/'runtime-r2-adaptations.json'").replace("R/'source/runtime_patcher.c'","R/'source/runtime_patcher_r2.c'")
src=src.replace("line='    mount none /system/bin/linkerconfig /apex/com.android.runtime/bin/linkerconfig bind\\n'","line='    mount none /system/etc/actual-runtime-bin /apex/com.android.runtime/bin bind\\n'")
src=src.replace("obs=obs.replace('#include <signal.h>','#include <signal.h>\\n#include <sys/wait.h>');", "obs=obs.replace('#include <signal.h>','#include <signal.h>\\n#include <sys/wait.h>\\n#include <sys/xattr.h>');obs=obs.replace('sleep(5);}', 'if(report>=0)fsync(report);sleep(5);}')\nobs=obs.replace('const char*paths[]={', 'const char*paths[]={\\\"/sys/class/block/vda/ro\\\",\\\"/sys/class/block/vdb/ro\\\",')\nobs=obs.replace('DIR *proc=opendir', 'char node_label[256]={0};ssize_t node_len=getxattr(\\\"/dev/block/vda\\\",\\\"security.selinux\\\",node_label,255);printf(\\\"DATA_NODE_CONTEXT bytes=%zd errno=%d value=%s\\\\n\\\",node_len,errno,node_label);struct stat node_stat;int node_rc=stat(\\\"/dev/block/vda\\\",&node_stat);printf(\\\"DATA_NODE_DAC rc=%d mode=%o uid=%u gid=%u\\\\n\\\",node_rc,node_rc?0:node_stat.st_mode,node_rc?0:node_stat.st_uid,node_rc?0:node_stat.st_gid);DIR *proc=opendir')\n")
# Add only the explicitly authorized fixture mapping to the actual consumed vendor text.
src=src.replace("(I/'observer.rc').write_text", "(I/'vendor.contexts').write_bytes((R/'inputs/root-enabled-vendor.contexts').read_bytes()+b'\\n/dev/block/vda    u:object_r:userdata_block_device:s0\\n')\n(I/'observer.rc').write_text")
src=src.replace("(I/'patch-initramfs.cpio.gz').write_bytes(cpio(prep));new=[]", "prep += [ent('runtime-bin',b'',0o40755),ent('vendor.contexts',(I/'vendor.contexts').read_bytes(),0o100644)]\nfor name in ['linker','linker64','crash_dump32','crash_dump64','linkerconfig']:\n value=(I/'candidate').read_bytes() if name=='linkerconfig' else (R/'inputs/runtime-bin-preserved'/name).read_bytes();prep.append(ent('runtime-bin/'+name,value,0o100644))\n(I/'patch-initramfs.cpio.gz').write_bytes(cpio(prep));new=[]")
src=src.replace("(I/'system-data-label').write_bytes", "(I/'root-data-label').write_bytes(b'u:object_r:system_data_root_file:s0\\0');(I/'system-data-label').write_bytes")
src=src.replace("commands_text=['mkdir /local'", "commands_text=[f'ea_set -f {I}/root-data-label / security.selinux','mkdir /local'")
src=src.replace("modified=['system/vendor/etc/fstab.mt8163','system/etc/init/hw/init.rc']", "modified=['system/vendor/etc/fstab.mt8163','system/etc/init/hw/init.rc','system/vendor/etc/selinux/vendor_file_contexts']")
# Actual vendor context text comes directly from admitted raw, not the source candidate containing three physical mappings.
fd_old=fd;os.close(fd);raw=Path('/srv/android/asus-root-enabled-incremental-r1/host-r2/validation/system-partition.raw');fd=os.open(raw,os.O_RDONLY|os.O_NOFOLLOW);cache={};(R/'inputs/root-enabled-vendor.contexts').write_bytes(get('system/vendor/etc/selinux/vendor_file_contexts'));os.close(fd)
(R/'source/prepare_runtime_r2_actual.py').write_text(src);exec(compile(src,str(R/'source/prepare_runtime_r2_actual.py'),'exec'))
