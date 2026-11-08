from pathlib import Path
import subprocess as s,shutil,json,hashlib,resource,os
R=Path('/srv/android/asus-sdk37-lmkd-functional');P=Path('/srv/android/asus-firstboot-runtime');I=R/'inputs/fixture-r4';I.mkdir();root=I/'root';shutil.copytree(P/'inputs/boot-r10/root',root,symlinks=True)
# Genuine first-stage init/policy/property contexts; fixture-only service graph and mounts.
for f in (R/'inputs/native-r2').iterdir():
 if f.suffix in ['.json','.readelf']:continue
 dest=root/'system'/('lib64' if f.name.endswith('.so') else 'bin')/f.name;shutil.copyfile(f,dest);dest.chmod(0o755)
for n in ['libc.so','libm.so','libdl.so']:shutil.copyfile(root/'system/lib64'/n,root/'system/lib64/bootstrap'/n)
shutil.copyfile(root/'system/bin/linker64',root/'system/bin/bootstrap/linker64')
cmd=['aarch64-linux-gnu-gcc','-static','-O2','-Wall','-Wextra','-Werror',str(R/'source/daemon_observer.c'),'-o',str(root/'system/bin/firstboot-observer')]
def limits():
 os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(60,60))
p=s.run(cmd,capture_output=True,text=True,preexec_fn=limits);(I/'compile.json').write_text(json.dumps(dict(argv=cmd,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr),indent=2));assert p.returncode==0,p.stderr
props=root/'system/etc/prop.default';p=props.read_text() if props.exists() else '';keys={'ro.config.low_ram':'true','ro.config.per_app_memcg':'false','ro.lmk.use_minfree_levels':'false','ro.lmk.use_new_strategy':'true','ro.lmk.debug':'true'}
p='\n'.join(l for l in p.splitlines() if l.split('=')[0] not in keys)+'\n'+''.join(k+'='+v+'\n' for k,v in keys.items());props.write_text(p)
(root/'system/etc/init/hw/init.rc').write_text('''on early-init
    mkdir /linkerconfig/bootstrap 0755
    write /linkerconfig/bootstrap/ld.config.txt \\#
    start ueventd

on init
    mkdir /dev/socket 0755 root root
    chmod 0666 /dev/kmsg
    mount tmpfs tmpfs /data mode=0755

on late-init
    trigger post-fs
    trigger boot

on post-fs
    write /sys/block/zram0/comp_algorithm lz4
    swapon_all /vendor/etc/fstab.memory

on boot
    start memory-observer
    start lmkd

service ueventd /system/bin/ueventd
    class core
    user root
    seclabel u:r:ueventd:s0

service memory-observer /system/bin/firstboot-observer
    user root
    group root system log readproc
    seclabel u:r:su:s0
    socket logdw dgram+passcred 0222 logd logd u:r:logd:s0
    disabled
    oneshot

service lmkd /system/bin/lmkd
    class core
    user lmkd
    group lmkd system readproc
    capabilities DAC_OVERRIDE KILL IPC_LOCK SYS_NICE SYS_RESOURCE
    socket lmkd seqpacket+passcred 0660 system system
    task_profiles ServiceCapacityLow
    disabled
    oneshot
''')
(root/'system/vendor/etc/fstab.memory').write_text('/dev/block/zram0 none swap defaults wait,zramsize=536870912\n')
(I/'fstab.mt8163').write_text('/dev/block/vda /system ext4 ro wait,first_stage_mount\n')
manifest=[]
for f in root.rglob('*'):
 if f.is_file() and not f.is_symlink():manifest.append(dict(path=str(f.relative_to(root)),bytes=f.stat().st_size,sha256=hashlib.sha256(f.read_bytes()).hexdigest()))
(I/'root-manifest.json').write_text(json.dumps(manifest,indent=2));print('root files',len(manifest),'bytes',sum(x['bytes'] for x in manifest))
