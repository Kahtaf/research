from pathlib import Path
import hashlib,json,re
R=Path(__file__).resolve().parents[1];E=R/'evidence';log=(R/'run-runtime-1/serial.log').read_bytes();text=log.decode();status=json.loads((R/'run-runtime-1/status.json').read_text());audit=json.loads((E/'cow-block-audit.json').read_text());seal=json.loads((E/'seal.json').read_text());pins=json.loads((E/'input-pins.json').read_text());block=json.loads((E/'blocker-inspection.json').read_text());ram=json.loads((E/'ramdisk-deltas.json').read_text())
checks={
 'serial_exact_export':hashlib.sha256(log).hexdigest()==seal['serial_sha256'],
 'actual_first_stage':'init first stage started!' in text,
 'actual_second_stage':'init second stage started!' in text,
 'selinux_policy_load':'Loading SELinux policy' in text,
 'enforcing_requested':'androidboot.selinux=enforcing' in text,
 'actual_selinux_denial':'SELinux permission check failed (source_context=u:r:vendor_init:s0' in text,
 'system_backend_vdb':'__mount(source=/dev/block/vdb,target=/system,type=ext4)=0: Success' in text,
 'data_backend_vda':'__mount(source=/dev/block/vda,target=/data,type=ext4)=0: Success' in text,
 'genuine_apexd_bootstrap':'apexd: Started. subcommand = --bootstrap' in text,
 '39_apexes_scanned':'Successfully scanned 39 preinstalled APEXes' in text,
 'four_bootstrap_packages':'Activated 4 packages.' in text,
 'four_erofs_mounts':len(re.findall(r'erofs: .*mounted with opts:',text))==4,
 'bootstrap_exits_0':bool(re.search(r"Service 'apexd-bootstrap'.*exited with status 0",text)),
 'runtime_apex_pin':block['selected_actual_files']['system/apex/com.android.runtime.apex']['sha256']=='638361e8de6863d070e491914a75e5e5b3a07ee2929bb6b048fe5f3bbdab403d',
 'first_fatal_linkerconfig_duplicate':'duplicate: heapprofd_client_api.so is provided by default and system in [vendor]' in text and 'Fatal signal 6 (SIGABRT)' in text,
 'fatal_precedes_observer':text.index('Fatal signal 6 (SIGABRT)')<text.index("starting service 'actual-runtime-observer'"),
 'real_managers_started':all("starting service '"+name+"'" in text for name in ['servicemanager','hwservicemanager']),
 'real_keymaster_started':"starting service 'vendor.keymaster-4-0'" in text,
 'keystore_exit_1_preserved':bool(re.search(r"Service 'keystore2'.*exited with status 1",text)),
 'maintenance_dependency_wait_preserved':'Waited one second for android.security.maintenance' in text,
 'true_post_data_apexd_not_observed':"starting service 'apexd'" not in text,
 'no_observer_stdout_claim':'FIRSTBOOT_OBSERVER_BEGIN' not in text and 'IPC_FUNCTIONAL_PING' not in text,
 'genuine_waits_preserved':all(block['genuine_waits_present'].values()),
 'root_failure_preserved':'ro.debuggable=0' in block['build_props_selected'],
 'bounded_runtime_timeout':status['timeout'] is True and status['wall_limit_seconds']==90,
 'base_raw_identity_unchanged':seal['raw_identity_unchanged'] and status['raw_identity_unchanged'],
 'core_pins_reverified':all(x['unchanged'] for x in seal['pins_reverified'].values()),
 'cow_audit_no_unexpected_deltas':audit['passed'] and audit['unexpected']==[] and audit['changed_guest_4KiB_blocks']==17,
 'ramdisk_only_expected_changes':{x['path'] for x in ram['original_entries'] if x['before_sha256']!=x['after_sha256']}=={'init','fstab.mt8163'},
 'fresh_bounded_data_profile':(R/'run-runtime-1/data-format.json').exists() and seal['runtime_attempts']==1,
 'owned_storage_bound':seal['owned_allocated_bytes']<2*1024**3 and seal['owned_logical_bytes']<2*1024**3,
 'three_corrections_limit':seal['runtime_fixture_corrections_used']==3,
}
for name in ['boringssl_self_test32','boringssl_self_test64','boringssl_self_test32_vendor','boringssl_self_test64_vendor']:
 checks[name+'_exit_0']=bool(re.search("Service '"+name+r"'.*exited with status 0",text))
d={'checks':checks,'passed':all(checks.values()),'expected_observations_passed':sum(checks.values()),'checks_total':len(checks),'keystore_status1_count':len(re.findall(r"Service 'keystore2'.*exited with status 1",text)),'not_qualified':['direct /sys/fs/selinux/enforce=1 read','observer Binder/HIDL ping replies','Keymaster registration/hardware info/crypto','keystore2 registration/functional IPC','post-data APEX activation/trust/final namespaces','service-owned keystore.module_hash.sent','Android/framework/GMS/hardware/root/flash acceptance'],'observer_limitation':'stdio_to_kmsg was configured but no stdout markers reached serial on actual ro.debuggable=0; pid222 invalid-handle kernel negatives are not positive IPC proof','first_blocker':'linkerconfig aborts on duplicate heapprofd_client_api.so provider in vendor namespace','terminal_boundary':'90-second host timeout during real vdc earlyBootEnded / vold wait for android.security.maintenance; no source/build job state inferred'}
(E/'qualification.json').write_text(json.dumps(d,indent=2));print(json.dumps({k:v for k,v in d.items() if k!='checks'},indent=2));assert d['passed']
