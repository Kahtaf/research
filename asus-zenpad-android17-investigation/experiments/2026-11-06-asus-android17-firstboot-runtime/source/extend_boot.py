from pathlib import Path
import shutil,subprocess as s,json,hashlib,os
R=Path('/srv/android/asus-firstboot-runtime');T=Path('/srv/android/lineage24');I=R/'inputs/boot-r5';assert not I.exists();shutil.copytree(R/'inputs/boot-r4',I,symlinks=True);root=I/'root';manifest=[]
def put(src,dest):
 src=Path(src);b=src.read_bytes();assert b==src.read_bytes();dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(b);manifest.append(dict(source=str(src),path=str(dest.relative_to(I)),bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
os.symlink('/system/bin/init',root/'system/bin/ueventd')
B=T/'out/soong/.intermediates/system/core/rootdir'
for mod,dest in [('init.rc','system/etc/init/hw/init.rc'),('ueventd.rc','system/etc/ueventd.rc'),('init-perfetto.rc','system/etc/init/init-perfetto.rc')]:put(B/mod/'android_arm64_armv8-a'/mod,root/dest)
for n in ['cgroups.json','task_profiles.json']:
 put(T/'system/core/libprocessgroup/profiles'/n,root/'system/etc'/n)
for n in ['cgroups_28.json','cgroups_29.json','cgroups_30.json','task_profiles_28.json','task_profiles_29.json','task_profiles_30.json']:
 version=n.split('_')[-1][:-5];put(T/'system/core/libprocessgroup/profiles'/n,root/'system/etc/task_profiles'/('cgroups' if n.startswith('cgroups') else 'task_profiles')/(version+'.json'))
# Read-only instrumentation executed by genuine init in its existing domain.
# No policy permissions, service readiness or protected completion properties are changed.
(root/'system/etc/init/firstboot-observe.rc').write_text('''on early-init
    write /dev/kmsg FIRSTBOOT_ENFORCEMENT_BEGIN
    copy /sys/fs/selinux/enforce /dev/kmsg
    write /dev/kmsg FIRSTBOOT_INIT_SID_BEGIN
    copy /proc/1/attr/current /dev/kmsg
    write /dev/kmsg FIRSTBOOT_INIT_SID_END

on property:ro.cold_boot_done=true
    write /dev/kmsg FIRSTBOOT_GENUINE_COLDBOOT_DONE
    copy /sys/fs/selinux/enforce /dev/kmsg

on property:apexd.status=*
    write /dev/kmsg FIRSTBOOT_APEX_STATUS=${apexd.status}

on property:keystore.module_hash.sent=*
    write /dev/kmsg FIRSTBOOT_MODULE_HASH_STATUS=${keystore.module_hash.sent}
''')
(I/'extension-manifest.json').write_text(json.dumps(manifest,indent=2));print('extended boot inputs',len(manifest))
