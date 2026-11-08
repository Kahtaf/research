from pathlib import Path
import json,hashlib,datetime,os,re,difflib,subprocess
R=Path('/srv/android/asus-genuine-service-runtime')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
log=(R/'run-boot-r9/serial.log').read_text();old=(R/'run-boot-r2/serial.log').read_text();beforev=(R/'run-boot-r6/serial.log').read_text()
checks={
 'first_stage_real':'init first stage started!' in log,
 'second_stage_real':'init second stage started!' in log,
 'policy_enforcing':bool(re.search(r'path=/sys/fs/selinux/enforce bytes=\d+ value=1\b',log)),
 'init_sid':'value=u:r:init:s0' in log,
 'shell_sid':'value=u:r:shell:s0' in log,
 'servicemanager_sid':'value=u:r:servicemanager:s0' in log,
 'hwservicemanager_sid':'value=u:r:hwservicemanager:s0' in log,
 'apexd_bootstrap_genuine_exit0':"Service 'apexd-bootstrap'" in log and 'OnBootstrap done' in log,
 'adbd_capex_scanned':'Found pre-installed APEX /system/apex/com.android.adbd.capex' in log,
 'zero_bootstrap_packages_not_qualified':'Activated 0 packages' in log,
 'servicemanager_ping_reply':'IPC_REPLY path=/dev/binder handle=0 flags=0x0 bytes=0' in log,
 'hidl_base_ping_reply':'IPC_REPLY path=/dev/hwbinder handle=0 flags=0x0 bytes=4 first_i32=0' in log,
 'both_functional_pings':'IPC_FUNCTIONAL_PING servicemanager=1 hwservicemanager=1' in log,
 'hwsm_real_ready_property':'FIXTURE_HWSM_READY=true' in log,
 'hwsm_real_not_disabled':'FIXTURE_HWSM_DISABLED=false' in log,
 'invalid_handle_negative':'handle=123456 command=0x7211' in log,
 'property_allowed':'OBS_PROPERTY_ALLOWED rc=0' in log and 'name=debug.firstboot.runtime_probe length=8 value=observed' in log,
 'property_denied':'OBS_PROPERTY_FORBIDDEN rc=-1' in log and 'name=persist.firstboot_runtime.denied length=0 value=' in log,
 'missing_context_before': 'Check failed: gSehandle != nullptr' in old,
 'missing_context_fixed':'Loaded service context from:' in log and 'Check failed: gSehandle != nullptr' not in log,
 'vintf_negative_before': 'IPC_FUNCTIONAL_PING servicemanager=1 hwservicemanager=0' in beforev,
 'mandatory_selftest_not_skipped':"Cannot find '/system/bin/boringssl_self_test32'" in log and 'reboot,boringssl-self-check-failed' in log,
 'framework_boot_completed_unset':'name=sys.boot_completed length=0 value=' in log,
 'keystore_completion_not_forged':'name=keystore.module_hash.sent length=0 value=' in log,
}
assert all(checks.values()),checks
policy=R/'inputs/boot-r9/root/system/vendor/etc/selinux/precompiled_sepolicy'
assert sha(policy)=='f2559923357169800212cb33c8a931dabe6ce02b56f372e43627e2e532728033'
receipts={}
for d in sorted(R.glob('run-boot-r*')):
 st=json.loads((d/'status.json').read_text());assert st['returncode']==0 and not st['timeout'];receipts[d.name]=dict(status=st,started=json.loads((d/'started.json').read_text()),serial_sha256=sha(d/'serial.log'))
result=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='partial_runtime_qualified_official_product_artifacts_blocked',checks=checks,expected_observations=len(checks),all_passed=True,current_pinned_policy=dict(bytes=policy.stat().st_size,sha256=sha(policy),version=30,byte_exact_recompiled=True),runs=receipts,invalid_run='run-boot-r4 used inherited prior probe after revised probe compile failed; no new probe claim is based on r4',scope='Real enforcing init + functional Binder/HIDL manager pings and property IPC. Keymaster registration/crypto, keystore handoff, post-data APEX/trust, authenticated adbd, framework/SystemUI/GMS/hardware are unproved.',physical_GO=False,framework_boot=False,authenticated_adbd=False)
(R/'evidence/qualification-final.json').write_text(json.dumps(result,indent=2))
# Complete owned input identity including executable modes and symlinks; no active out reads.
manifest=[]
for base in [R/'inputs',R/'source']:
 for f in sorted(base.rglob('*')):
  row=dict(path=str(f.relative_to(R)))
  if f.is_symlink():row.update(kind='symlink',target=os.readlink(f))
  elif f.is_file():row.update(kind='file',bytes=f.stat().st_size,mode=oct(f.stat().st_mode&0o7777),sha256=sha(f))
  else:continue
  manifest.append(row)
(R/'evidence/owned-input-hashes-final.json').write_text(json.dumps(manifest,indent=2))
outputs=[]
for d in sorted(R.glob('run-boot-r*')):
 for f in d.iterdir():
  if f.is_file():outputs.append(dict(path=str(f.relative_to(R)),bytes=f.stat().st_size,sha256=sha(f)))
(R/'evidence/owned-output-hashes-final.json').write_text(json.dumps(outputs,indent=2))
# Save observable preparation failures without inventing missing timestamps or source receipts.
(R/'evidence/preparation-failures.json').write_text(json.dumps(dict(capture_more='Observed AssertionError at source line16: late supplemental compiled policy differs from qualified prior policy; supplemental files quarantined and never runtime-consumed. Current policy was later independently reproduced from the original capture-r1.',probe_r4='Actual compiler stderr and command retained in observer-r4-compile.json. Run r4 used prior ELF and is excluded from new probe claims. Corrected probe compiled successfully in observer-r5-compile.json.',vintf_r8='Preparation failed before generation: system_manifest.xml was sought in an assumed .8 Ninja shard. No QEMU run r8 exists. Corrected preparation r9 used the shard recorded in vintf-module-rules.json.',preparation_r1='Temporary variable reused in current_init_rc metadata field; original receipt preserved with preparation-r1-errata.json; no runtime input affected.',qualification_parser_r1='Original qualification.json expected enforce read length2; actual selinuxfs read returns length1. Final parser accepts numeric read length and verifies value1 against raw log.'),indent=2))
# Keep a small source diff explaining old/current compiled policy provenance.
a=(R/'inputs/boot-r5/root/system/vendor/etc/selinux/vendor_sepolicy.cil').read_text().splitlines(True);b=(R/'inputs/boot-r9/root/system/vendor/etc/selinux/vendor_sepolicy.cil').read_text().splitlines(True)
(R/'evidence/vendor-policy-cil-delta.diff').write_text(''.join(difflib.unified_diff(a,b,fromfile='qualified-prior-vendor.cil',tofile='capture-r1-vendor.cil')))
# Functional probes do not register a substitute service. Record only the genuine manager calls.
print(json.dumps(dict(status=result['status'],observations=len(checks),runs=len(receipts),input_files=len(manifest),output_files=len(outputs),all_passed=True),indent=2))
