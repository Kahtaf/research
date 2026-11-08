from pathlib import Path
import json,hashlib,datetime,os,re,subprocess,shutil,tarfile
R=Path('/srv/android/asus-genuine-service-runtime');P=Path('/srv/android/asus-firstboot-runtime')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
# Never reopen active AOSP/out. The late supplemental capture failed equality
# to the qualified inputs and is quarantined, not mixed into any guest.
I=R/'inputs/capture-r2';root=R/'inputs/boot-r5/root';identity=[]
for rel,dest in [('system/core/init/init_first_stage/android_ramdisk_arm64_armv8-a/init',R/'inputs/boot-r5/init_first_stage'),('system/core/init/init_second_stage/android_arm64_armv8-a/init',root/'system/bin/init'),('system/sepolicy/precompiled_sepolicy/android_common/p00a/precompiled_sepolicy',root/'system/vendor/etc/selinux/precompiled_sepolicy'),('system/linkerconfig/linkerconfig/android_arm64_armv8-a/linkerconfig',root/'system/bin/linkerconfig')]:
 src=I/'out/soong/.intermediates'/rel;identity.append(dict(supplemental=str(src),runtime=str(dest),supplemental_sha256=sha(src),runtime_sha256=sha(dest),equal=sha(src)==sha(dest)))
(R/'evidence/supplemental-capture-quarantine.json').write_text(json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),reason='capture_more.py aborted equality assertion; original copying before/after comparisons passed transiently but no successful capture receipt was written; supplemental files excluded from all runtime inputs',runtime_identity=identity,files=[dict(path=str(f.relative_to(I)),bytes=f.stat().st_size,sha256=sha(f)) for f in I.rglob('*') if f.is_file()],active_out_reopened=False),indent=2))
parity=json.loads((R/'inputs/provenance/combined-parity.json').read_text());K=P/'kernel-cpuset-r1';sources=[dict(path=x['path'],expected=x['r7_source_sha256'],actual=sha(K/x['path'])) for x in parity['sources']]
cfg={}
for l in (R/'inputs/kernel-r7/config').read_text().splitlines():
 if l.startswith('CONFIG_'):k,v=l.split('=',1);cfg[k]=v
 elif l.startswith('# CONFIG_') and l.endswith(' is not set'):cfg[l.split()[1]]='n'
options=[dict(option=x['option'],expected=x['r7'],actual=cfg.get(x['option'],'n')) for x in parity['selected_config']]
assert all(x['expected']==x['actual'] for x in sources+options)
(R/'evidence/kernel-scope-verification.json').write_text(json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),virtual_kernel_image=sha(R/'inputs/kernel-r7/Image'),virtual_kernel_config=sha(R/'inputs/kernel-r7/config'),sources=sources,options=options,parent_acceptance_sha256=sha(R/'inputs/provenance/inherited-parent-firstboot-parity-acceptance.json'),physical_correspondence='Inherited timestamped parent equality receipt for physical e9cde06e...; rechecked virtual selected pins only; physical kernel not executed',whole_kernel_equivalence=False),indent=2))
(R/'evidence/preparation-r1-errata.json').write_text(json.dumps(dict(field='current_init_rc',reason='prepare.py reused temporary a for a later ICU dependency; correct frozen core init identity follows',boot_r1_init_rc_sha256=sha(R/'inputs/boot-r1/root/system/etc/init/hw/init.rc'),late_current_output_is_quarantined=True),indent=2))
manifest=[]
for base in ['inputs/capture-r1','inputs/kernel-r7','inputs/boot-r1','inputs/boot-r2','inputs/boot-r3','inputs/boot-r4','inputs/boot-r5','inputs/service-contexts-r1','inputs/observer-r1','source']:
 for f in sorted((R/base).rglob('*')):
  row=dict(path=str(f.relative_to(R)))
  if f.is_symlink():row.update(kind='symlink',target=os.readlink(f))
  elif f.is_file():row.update(kind='file',bytes=f.stat().st_size,mode=oct(f.stat().st_mode&0o7777),sha256=sha(f))
  else:continue
  manifest.append(row)
(R/'evidence/owned-input-hashes.json').write_text(json.dumps(manifest,indent=2))
outputs=[]
for d in sorted(R.glob('run-boot-r*')):
 st=json.loads((d/'status.json').read_text());assert not st['timeout'] and st['returncode']==0
 for n in ['initramfs.cpio.gz','system.ext4','data.ext4','seed-exec','serial.log','command.json']:
  f=d/n;outputs.append(dict(path=str(f.relative_to(R)),bytes=f.stat().st_size,sha256=sha(f)))
(R/'evidence/owned-output-hashes.json').write_text(json.dumps(outputs,indent=2))
log=(R/'run-boot-r5/serial.log').read_text();negative=(R/'run-boot-r2/serial.log').read_text()
checks={
 'genuine_first_stage': 'init first stage started!' in log,
 'genuine_second_stage':'init second stage started!' in log,
 'enforcing_observed':'path=/sys/fs/selinux/enforce bytes=2 value=1' in log,
 'init_sid':'value=u:r:init:s0' in log,
 'shell_sid':'value=u:r:shell:s0' in log,
 'servicemanager_sid':'value=u:r:servicemanager:s0' in log,
 'hwservicemanager_sid':'value=u:r:hwservicemanager:s0' in log,
 'genuine_apexd_exec_exit0':"Service 'apexd-bootstrap'" in log and 'OnBootstrap done' in log,
 'actual_adbd_capex_scanned':'Found pre-installed APEX /system/apex/com.android.adbd.capex' in log,
 'zero_bootstrap_activation_not_success':'Activated 0 packages' in log,
 'servicemanager_real_ping_reply':'IPC_REPLY path=/dev/binder handle=0 flags=0x0 bytes=0' in log,
 'invalid_handle_failed_reply':'handle=123456 command=0x7211' in log,
 'property_allowed':'OBS_PROPERTY_ALLOWED rc=0' in log and 'name=debug.firstboot.runtime_probe length=8 value=observed' in log,
 'property_denied':'OBS_PROPERTY_FORBIDDEN rc=-1' in log and 'name=persist.firstboot_runtime.denied length=0 value=' in log,
 'missing_context_before':'Check failed: gSehandle != nullptr' in negative,
 'missing_context_fixed':'Loaded service context from:' in log and 'Check failed: gSehandle != nullptr' not in log,
 'mandatory_selftest_preserved':"Cannot find '/system/bin/boringssl_self_test32'" in log and 'reboot,boringssl-self-check-failed' in log,
 'boot_completed_unset':'name=sys.boot_completed length=0 value=' in log,
 'hwsm_not_qualified':'IPC_FUNCTIONAL_PING servicemanager=1 hwservicemanager=0' in log,
}
(R/'evidence/qualification.json').write_text(json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),checks=checks,all_expected_observations=all(checks.values()),remaining_gates=['platform BoringSSL self-tests','signed selected com.android.runtime APEX/bootstrap linkerconfig','assembled system_ext/vendor VINTF manifests','genuine generated system/system_ext/product properties and apexkeys','HIDL manager/Keymaster registration and calls','keystore crypto/module hash handoff','post-data APEX activation and trust','adbd execution from activated package and isolated positive/negative authentication'],scope='Partial prerequisite qualification, not full service chain, framework, GMS, physical hardware or flash readiness',r4_invalid_probe_revision=True),indent=2))
print(json.dumps(dict(checks=checks,files=len(manifest),outputs=len(outputs),quarantine_identity=identity),indent=2))
