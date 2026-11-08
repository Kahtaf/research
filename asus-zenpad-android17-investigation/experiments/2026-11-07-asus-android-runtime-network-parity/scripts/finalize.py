from pathlib import Path
import json,hashlib,re
L=Path(__file__).resolve().parents[1];E=L/'evidence'
build=json.loads((E/'build-result.json').read_text());runtime=json.loads((L/'run-runtime/status.json').read_text());pins=json.loads((L/'integration/pins.json').read_text());pipeline=json.loads((E/'startup-pipeline-result.json').read_text());receipt=json.loads((E/'base-unchanged-receipt.json').read_text())
serial=(L/'run-runtime/serial.log').read_text(errors='replace');public=(E/'public-report-compact.txt').read_text(errors='replace')
assert build['returncode']==0 and build['genuine_build_success'] and build['five_postimages_after']==pins['combined_post']
assert hashlib.sha256((E/'original.config').read_bytes()).hexdigest()==hashlib.sha256((E/'built.config').read_bytes()).hexdigest()==pins['preserve_android_config_sha256']
assert pipeline['actual_os_boots']==1 and receipt['base_unchanged'] and receipt['boot_unchanged']
assert 'NetBpfLoad: done, transferring control to uprobestatsbpfload.' in serial
assert '=== CRITICAL FAILURE LOADING BPF PROGRAMS FROM /vendor/etc/bpf ===' in serial
assert not re.search(r"starting service 'zygote",serial)
assert not re.search(r'^PUBLIC_PROP bpf.progs_loaded \S+',public,re.M)
need=['Linux version','Activated 39','Wait for property','NetBpfLoad:','UprobeStatsBpfLoad:','BpfLoader-rs:','BpfLoader:','Service \'bpfloader\'','Service bpfloader','shutdown_command','PERFMON','bpf_jit: *** NOT YET']
events=[f'{i}: {x}' for i,x in enumerate(serial.splitlines(),1) if any(n in x for n in need)]
(E/'boot-boundary-lines.txt').write_text('\n'.join(events)+'\n')
public_events=[f'{i}: {x}' for i,x in enumerate(public.splitlines(),1) if x.startswith('PUBLIC_PROP') or x.startswith('PUBLIC_READ /sys/fs/selinux/enforce') or 'On-device signing done.' in x or 'odrefresh terminated by exit(80)' in x or 'odrefresh compiled all artifacts, returned 80' in x]
(E/'observer-boundary-lines.txt').write_text('\n'.join(public_events)+'\n')
d={
 'status':'ONE_BUILD_SUCCEEDED_ONE_ACTUAL_BOOT_STOPPED_FATAL_PLATFORM_VENDOR_BPF',
 'remote_prefix':'/srv/android/asus-android-runtime-network-parity-20261107',
 'compile_invocations':1,'actual_os_boots':1,'additional_syscall_or_network_suites':0,
 'kernel':{'path':'/srv/android/asus-android-runtime-network-parity-20261107/build/arch/arm64/boot/Image','sha256':build['image_sha256'],'bytes':build['image_bytes'],'compile_exit':0,'compile_seconds':build['elapsed_wall_seconds'],'source_origin':'/srv/android/asus-firstboot-runtime/kernel-cpuset-r1','config_origin':'/srv/android/asus-firstboot-runtime/kernel-build-r7/.config','config_sha256':build['config_after'],'full_config_byte_identical':True,'qualified_five_postimages':build['five_postimages_after'],'patches_applied_fuzz_zero_no_offsets':True},
 'system':{'sha256':'fff09d5ab4e0ca301786830d133106152c4c0aca15a2c49166c28827aa5e3f79','bytes':3753902080,'receipt_metadata_identical':True,'new_full_hash_or_copy':False},
 'boot':{'sha256':'784d4dc565e7742ea607683d2a67d1fdb066764bddfa369895cbaaf6f048b435','bytes':9242624,'receipt_metadata_identical':True,'new_full_hash_or_copy':False},
 'runtime':{'limit_seconds':600,'elapsed_seconds':runtime['elapsed_wall_seconds'],'timeout':False,'qemu_exit':runtime['returncode'],'termination':runtime['termination'],'vcpus':2,'memory_MiB':2048,'nic':False,'usb':False,'no_reboot':True,'rlimit_as_added':False,'apex_packages':39,'odsign_original_key_wait_completed_guest_seconds':377.069012,'odsign_key_wait_ms':284278,'odrefresh_exit':80,'on_device_signing_done':True,'odsign_key_done':'1','odsign_verification_done':'1','selinux_enforcing_observed':True,'netbpfload_done_guest_seconds':378.440850,'bpf_progs_loaded':'unset in observer samples','zygote_started':False,'framework_started':False},
 'first_critical_loader_failure':{'stage':'platform BpfLoader','object':'/vendor/etc/bpf/filterPowerSupplyEvents.o','program':'skfilter_power_supply','operation':'BPF_PROG_LOAD','errno':7,'errno_name':'E2BIG','message':'Argument list too long','prog_load_failure_guest_seconds':379.073000,'critical_banner_guest_seconds':379.077008,'service_exit':121,'service_exit_guest_seconds':399.096286,'init_fatal_confirmation_guest_seconds':399.109735,'precise_syscall_rejection_cause':'not isolated by this boot'},
 'stop_delay_limitation':'Supervisor detected init reboot_on_failure confirmation at 399.109735s, approximately 20.033s after explicit platform-loader critical banner; no second boot or automatic fix.',
 'other_observed_errors':['Optional UprobeStats program loads E2BIG and map creates EINVAL; chain continued','Platform Rust BPF loader object errors before critical vendor object','UprobeStats init capability PERFMON unsupported','Early aconfig metadata/storage errors','lmkd missing memory-cgroup support','BPF JIT opcode c3 warning'],
 'scope':{'active_sources_and_outputs_untouched':True,'hardware_device_adb_or_root_helpers':False,'cloud_lifecycle_actions':False,'other_owner_processes_inspected_or_signalled':False,'candidate_binary_or_APEX_overlays':False,'readiness_setters_or_hal_stubs':False,'private_data_or_calibration_access':False,'DATA_entropy_or_generated_keys_exported':False,'whole_os_or_hardware_success_claim':False},
 'next_concrete_boundary':'Isolate the real BPF_PROG_LOAD E2BIG rejection for final vendor filterPowerSupplyEvents.o on this exact preserved-config Image; establish which loader attributes/kernel limits reject it before proposing a narrowly scoped compatibility change. Optional stats failures are separate. No further build/boot in this authorization.',
 'evidence':{'build':'evidence/build-result.json','integration':'evidence/integration.json','config':'evidence/built.config','serial':'run-runtime/serial.log','boundary_lines':'evidence/boot-boundary-lines.txt','public_observer':'evidence/public-report-compact.txt','observer_boundary':'evidence/observer-boundary-lines.txt','base_identity':'evidence/base-unchanged-receipt.json','adaptations':'evidence/adaptations.json'}
}
(L/'HANDOFF.json').write_text(json.dumps(d,indent=2)+'\n')
print(json.dumps({'kernel_sha256':d['kernel']['sha256'],'config_sha256':d['kernel']['config_sha256'],'first_critical':d['first_critical_loader_failure'],'runtime_seconds':runtime['elapsed_wall_seconds'],'serial_bytes':len(serial),'public_bytes':len(public)},indent=2))
