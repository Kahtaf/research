from pathlib import Path
import os,json,gzip,hashlib,struct,subprocess as s,stat
R=Path('/srv/android/asus-vendor-bpf-load-compat-20261107');I=R/'inputs';E=R/'evidence';G=Path('/srv/android/asus-genuine-service-runtime');OLD=Path('/srv/android/asus-r9-actual-early-runtime-20261106');P=Path('/srv/android/asus-r9-linkerconfig-ownership-fix-20261106');raw=Path(json.loads((E/'admission.json').read_text())['system']['path']);os.environ['TMPDIR']=str(R/'tmp');os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});commands=[]
def run(cmd):
 p=s.run([str(x) for x in cmd],capture_output=True,text=True,timeout=60);commands.append(dict(command=[str(x) for x in cmd],rc=p.returncode,stdout=p.stdout,stderr=p.stderr));(E/'prepare-commands.json').write_text(json.dumps(commands,indent=2));assert p.returncode==0,p.stderr;return p
build=json.loads((E/'kernel-selection.json').read_text());assert build['reused_qualified_image']
assert hashlib.sha256((R/'build/arch/arm64/boot/Image').read_bytes()).hexdigest()==build['image_sha256']
assert hashlib.sha256((R/'build/.config').read_bytes()).hexdigest()=='c2ea1277e1574da39d1d55d31bde7bda439ab624561ad3c6a6f4730e38f57834'
assert hashlib.sha256((G/'run-boot-r9/seed-exec').read_bytes()).hexdigest()=='eddd78f4558e38ba1a1b5f2d9a8420111859e70a1d9c0d3b9cd837a4207ecf60'
ram=(OLD/'inputs/actual-ramdisk.cpio.gz').read_bytes();assert hashlib.sha256(ram).hexdigest()=='95f5c2a8aded2e081e30e72ebd37322a24aa895bbe7e334c79c1381bcd3fe240';b=gzip.decompress(ram);pos=0;entries=[]
while True:
 head=b[pos:pos+110];f=[int(head[6+8*i:14+8*i],16) for i in range(13)];n=b[pos+110:pos+110+f[11]-1].decode();pos=(pos+110+f[11]+3)//4*4;v=b[pos:pos+f[6]];pos=(pos+f[6]+3)//4*4
 if n=='TRAILER!!!':break
 entries.append((n,f,v))
actualinit=next(v for n,f,v in entries if n=='init');assert hashlib.sha256(actualinit).hexdigest()=='b2abeeb7dc01d884536dd38ebccd835a8589187a979cf84e51d78131ce800ed4'
def mapfstab(b):
 for a,z in [(b'/dev/block/platform/soc/11230000.mmc/by-name/system',b'/dev/block/vdb'),(b'/dev/block/platform/soc/11230000.mmc/by-name/userdata',b'/dev/block/vda')]:assert b.count(a)==1;b=b.replace(a,z)
 return b
(I/'vendor.fstab').write_bytes(mapfstab((I/'original-vendor.fstab').read_bytes()))
ctx=(I/'original-vendor.contexts').read_bytes();line=b'\n/dev/block/vda    u:object_r:userdata_block_device:s0\n';assert b'/dev/block/vda ' not in ctx;(I/'vendor.contexts').write_bytes(ctx+line)
(I/'observer.rc').write_text('service actual-runtime-observer /system/bin/actual-runtime-observer\n    class core\n    user shell\n    group shell log readproc\n    seclabel u:r:shell:s0\n    disabled\n    oneshot\n    stdio_to_kmsg\n\non early-init\n    start actual-runtime-observer\n')
run(['aarch64-linux-gnu-gcc','-static','-O2','-Wall','-Wextra','-Werror',R/'source/observer.c','-o',I/'observer'])
p=(R/'source/patcher.c').read_text();run(['aarch64-linux-gnu-gcc','-static','-O2','-Wall','-Wextra','-Werror',R/'source/patcher.c','-o',I/'patcher'])
def ent(n,v,mode):return n,[1,mode,0,0,1,0,len(v),0,0,0,0,len(n)+1,0],v
def cpio(rows):
 a=bytearray()
 for n,f,v in rows+[ent('TRAILER!!!',b'',0)]:
  f=f.copy();nb=n.encode()+b'\0';f[6]=len(v);f[11]=len(nb);a+=b'070701'+''.join(f'{x:08x}' for x in f).encode()+nb;a+=b'\0'*(-len(a)%4);a+=v;a+=b'\0'*(-len(a)%4)
 return gzip.compress(a,mtime=0)
prep=[ent(n,(I/file).read_bytes(),0o100755 if n=='init' else 0o100644) for n,file in [('init','patcher'),('vendor.fstab','vendor.fstab'),('vendor.contexts','vendor.contexts'),('observer','observer'),('observer.rc','observer.rc'),('candidate-lib','libbpf_android.candidate.so')]];(I/'patch-initramfs.cpio.gz').write_bytes(cpio(prep));new=[]
for n,f,v in entries:
 if n=='init':v=(G/'run-boot-r9/seed-exec').read_bytes()
 if n=='fstab.mt8163':v=mapfstab(v)
 new.append((n,f,v))
new += [ent('first-stage-init',actualinit,0o100750),ent('entropy.seed',os.urandom(64),0o100400)];(I/'runtime-initramfs.cpio.gz').write_bytes(cpio(new));os.chmod(I/'runtime-initramfs.cpio.gz',0o400)
c=65536;size=raw.stat().st_size;back=str(raw).encode();l1=(size+c*(c//8)-1)//(c*(c//8))
with (I/'system.qcow2').open('xb') as f:f.write(struct.pack('>IIQIIQIIQQIIQ',0x514649fb,2,72,len(back),16,size,0,l1,3*c,c,1,0,0)+back);f.seek(c);f.write(struct.pack('>Q',2*c));f.seek(2*c);f.write(struct.pack('>4H',1,1,1,1));f.truncate(4*c)
data=I/'data.ext4';data.touch(exist_ok=False);os.truncate(data,2*1024**3);run(['mke2fs','-F','-t','ext4','-b','4096','-I','256','-O','none,has_journal,ext_attr,resize_inode,dir_index,filetype,extent,sparse_super,large_file,uninit_bg,dir_nlink,extra_isize','-E','lazy_itable_init=0,lazy_journal_init=0',data]);(I/'empty-report').write_text('')
for n,v in [('root','system_data_root_file'),('system','system_data_file'),('shell','shell_data_file')]: (I/(n+'-label')).write_bytes(('u:object_r:'+v+':s0\0').encode())
cmds=[f'ea_set -f {I}/root-label / security.selinux','mkdir /local','mkdir /local/tmp','set_inode_field /local mode 040751','set_inode_field /local uid 0','set_inode_field /local gid 2000','set_inode_field /local/tmp mode 040771','set_inode_field /local/tmp uid 2000','set_inode_field /local/tmp gid 2000',f'ea_set -f {I}/system-label /local security.selinux',f'ea_set -f {I}/shell-label /local/tmp security.selinux',f'write {I}/empty-report /local/tmp/actual-runtime-report.txt','set_inode_field /local/tmp/actual-runtime-report.txt mode 0100600','set_inode_field /local/tmp/actual-runtime-report.txt uid 2000','set_inode_field /local/tmp/actual-runtime-report.txt gid 2000',f'ea_set -f {I}/shell-label /local/tmp/actual-runtime-report.txt security.selinux'];(I/'data-prepare.debugfs').write_text('\n'.join(cmds)+'\n');run(['/usr/sbin/debugfs','-w','-f',I/'data-prepare.debugfs',data])
d=dict(candidate_runtime=True,candidate_overlay={'system/lib64/libbpf_android.so':hashlib.sha256((I/'libbpf_android.candidate.so').read_bytes()).hexdigest()},system_modified=['system/lib64/libbpf_android.so','system/vendor/etc/fstab.mt8163','system/vendor/etc/selinux/vendor_file_contexts'],system_added=['system/bin/actual-runtime-observer','system/etc/init/actual-runtime-observer.rc'],boot_changes=['seed-exec wrapper executes original first-stage init after fresh entropy input','fstab maps system=vdb userdata=vda'],userdata='fresh disposable 2GiB ext4; public scratch shell labels; all generated keys/entropy remain remote',context_addition=line.decode(),observer='static shell-domain read-only properties/process/logcat; no readiness writes',core_init_unchanged=True,APEX_unchanged=True,compiled_policy_unchanged=True,metadata_adapted=False,metadata_note='Actual final vendor fstab has no metadata backing; preserve product outcome, do not invent metadata readiness',guest=dict(vcpus=2,memory_MiB=2048,network=False,usb=False,wall_seconds=600))
(E/'adaptations.json').write_text(json.dumps(d,indent=2));print(json.dumps(d,indent=2))
