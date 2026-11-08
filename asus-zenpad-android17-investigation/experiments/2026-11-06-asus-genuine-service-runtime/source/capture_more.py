from pathlib import Path
import json,hashlib,shutil,subprocess,datetime,re,os
R=Path('/srv/android/asus-genuine-service-runtime');T=Path('/srv/android/lineage24');P=Path('/srv/android/asus-firstboot-runtime');I=R/'inputs/capture-r2';I.mkdir();rows=[]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def freeze(rel):
 src=T/rel;dst=I/rel;dst.parent.mkdir(parents=True,exist_ok=True);a=sha(src);shutil.copy2(src,dst);assert a==sha(dst)==sha(src);rows.append(dict(source=str(src),copy=str(dst),before=a,after=sha(src),bytes=src.stat().st_size))
for rel in ['out/soong/.intermediates/system/apex/apexd/apexd/android_arm64_armv8-a/unstripped/apexd','out/soong/.intermediates/system/hwservicemanager/hwservicemanager/android_arm64_armv8-a/unstripped/hwservicemanager','out/soong/.intermediates/system/security/keystore2/keystore2/android_arm64_armv8-a/unstripped/keystore2','out/soong/.intermediates/frameworks/native/cmds/servicemanager/servicemanager/android_arm64_armv8-a/unstripped/servicemanager','out/soong/.intermediates/hardware/interfaces/keymaster/4.0/default/android.hardware.keymaster@4.0-service/android_vendor_arm64_armv8-a_cfi/unstripped/android.hardware.keymaster@4.0-service','out/soong/.intermediates/system/core/init/init_first_stage/android_ramdisk_arm64_armv8-a/init','out/soong/.intermediates/system/core/init/init_second_stage/android_arm64_armv8-a/init','out/soong/.intermediates/system/sepolicy/precompiled_sepolicy/android_common/p00a/precompiled_sepolicy','out/soong/.intermediates/system/core/rootdir/init.rc/android_arm64_armv8-a/init.rc','out/soong/.intermediates/system/linkerconfig/linkerconfig/android_arm64_armv8-a/linkerconfig']:
 freeze(rel)
root=R/'inputs/boot-r5/root';identity=[]
for src,dest in [(I/'out/soong/.intermediates/system/core/init/init_first_stage/android_ramdisk_arm64_armv8-a/init',R/'inputs/boot-r5/init_first_stage'),(I/'out/soong/.intermediates/system/core/init/init_second_stage/android_arm64_armv8-a/init',root/'system/bin/init'),(I/'out/soong/.intermediates/system/sepolicy/precompiled_sepolicy/android_common/p00a/precompiled_sepolicy',root/'system/vendor/etc/selinux/precompiled_sepolicy'),(I/'out/soong/.intermediates/system/linkerconfig/linkerconfig/android_arm64_armv8-a/linkerconfig',root/'system/bin/linkerconfig')]:
 identity.append(dict(current_output=str(src),fixture=str(dest),current_sha256=sha(src),fixture_sha256=sha(dest),equal=sha(src)==sha(dest)))
assert all(x['equal'] for x in identity)
(R/'evidence/capture-r2.json').write_text(json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),files=rows,current_outputs_match_prior_fixture=identity),indent=2))
parity=json.loads((R/'inputs/provenance/combined-parity.json').read_text());K=P/'kernel-cpuset-r1';sources=[dict(path=x['path'],expected=x['r7_source_sha256'],actual=sha(K/x['path'])) for x in parity['sources']]
cfg={}
for l in (R/'inputs/kernel-r7/config').read_text().splitlines():
 if l.startswith('CONFIG_'):k,v=l.split('=',1);cfg[k]=v
 elif l.startswith('# CONFIG_') and l.endswith(' is not set'):cfg[l.split()[1]]='n'
options=[dict(option=x['option'],expected=x['r7'],actual=cfg.get(x['option'],'n')) for x in parity['selected_config']]
assert all(x['expected']==x['actual'] for x in sources+options)
(R/'evidence/kernel-scope-verification.json').write_text(json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),virtual_kernel_image=sha(R/'inputs/kernel-r7/Image'),virtual_kernel_config=sha(R/'inputs/kernel-r7/config'),sources=sources,options=options,parent_acceptance_sha256=sha(R/'inputs/provenance/inherited-parent-firstboot-parity-acceptance.json'),physical_correspondence='Inherited timestamped parent receipt for physical e9cde06e...; this run rechecks 290 virtual source files/134 virtual options against accepted pins; physical kernel not executed'),indent=2))
# Supplement the erroneous temporary-variable field in immutable preparation-r1.json.
(R/'evidence/preparation-r1-errata.json').write_text(json.dumps(dict(field='current_init_rc',reason='prepare.py reused temporary a for a later ICU dependency; correct core init identity below',actual_generated_init_rc_sha256=sha(I/'out/soong/.intermediates/system/core/rootdir/init.rc/android_arm64_armv8-a/init.rc'),boot_r1_init_rc_sha256=sha(R/'inputs/boot-r1/root/system/etc/init/hw/init.rc')),indent=2))
print('Captured',len(rows),'additional outputs;',len(sources),'sources and',len(options),'options verified')
