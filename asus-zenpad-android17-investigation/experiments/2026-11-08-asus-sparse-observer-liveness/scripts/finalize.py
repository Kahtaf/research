from pathlib import Path
import hashlib,json,stat

R=Path(__file__).resolve().parents[1]
B=R.parent/'2026-11-08-asus-arm64-delay-loop-observation'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda n:json.loads((R/'evidence'/n).read_text())
i=read('identity.json');p=read('packaging-receipt.json');elf=read('linked-capture.json');build=read('build-status.json')
assert build['status']=='complete' and build['compile_attempts']==1 and build['max_jobs']==8
assert elf['status']=='PASS_ACTUAL_SOURCE_AND_ELF_SPARSE_PROFILE'
assert elf['sparse_ready_publication_stlr_count']==0 and elf['old_ready_publication_stlr_count']==6
assert read('plan-isolation-receipt.json')['actual_installer_main_calls']==1
assert read('install-plan.json')['device_contacted'] is False
after=json.loads((R/'evidence/after.stdout').read_text())
assert after['id']=='8549823276971553556' and after['status']=='TERMINATED' and not (R/'s').exists()
for n,expected in read('parent-local-review.json')['reviewed'].items():assert sha(R/n)==expected
for n,v in read('source-pins.json').items():assert sha(R/'source'/n)==v['after']
for n in ['adb','legacy_adb.py','bootformat.py','fdt.py']:assert (R/'source'/n).read_bytes()==(B/'source'/n).read_bytes()
assert stat.S_IMODE((R/'source/adb').stat().st_mode)==0o755
remote=R.parent/'2026-11-06-asus-product-input-build-kit/scripts/remote.py'
assert sha(remote)=='c22884576a780cbb1ddf5e1b02f0b6e9d6eb5c25f8d9bc82fb077543f05cf4ab'
for name,key in [('candidate.img','candidate'),('candidate.p10.raw','full_p10'),('Image.gz-dtb','compiled_Image_gz_dtb'),('resolved.config','config'),('ramdisk.wrapped','ramdisk'),('runtime.dtb','runtime_DTB')]:
 assert sha(R/'artifacts'/name)==p[key]['sha256']
assert 'Reauthentication failed' in (R/'evidence/before.stderr').read_text()
assert read('handoff.auth-blocked.json')['kernel_build_attempts']==0

contract=dict(run_uuid=i['run_uuid'],entry_prefix='ASUS49-ENTRY run='+i['run_uuid'],mode=i['mode'],
    meaning='compile profile only; never readiness or passed liveness',helper_prefix=i['helper_prefix'],
    helper_event_suffixes=i['helper_event_suffixes'],helper_alarm_suffix=i['helper_alarm_suffix'],direct_markers=i['direct_markers'],
    hot_profile=dict(ready_pointers_published=False,retained_hot_area_bytes_reserved=0,old_six_protocols='deliberately absent; never admitted'),
    physical_admission=['exact full-p10 installed readback','fresh kernel entry and exact mode UUID','fresh stock boot identity','actual unchanged helper PID1/release/path/result records'],
    bounded_liveness='actual counter-target/delta>=1500000000 plus alarm flag or actual alarm marker plus complete after IRQ growth',
    iteration_cap='actual progress, not failed timer or full pass if reached before deadline',
    missing_final='unresolved publication/environment; does not exonerate instrumentation')
(R/'evidence/mode-contract.json').write_text(json.dumps(contract,indent=2)+'\n')
preservation=dict(status='PASS_SCOPED_PRESERVATION',changed_kernel_files=list(read('source-pins.json')),
    source_pins='source-pins.json',prepost_inodes='base-freeze.json / repository-preservation.json',
    unchanged_sources=elf['preserved_sources'],config=p['config'],wrapped_ramdisk=p['ramdisk'],helper=p['init'],
    DT_compiled=p['compiled_DTB'],DT_runtime=p['runtime_DTB'],bootargs=p['bootargs'],initrd=p['initrd'],layout=p['layout'],
    old_Image_image_size=18907136,new_Image_image_size=p['layout']['Image_image_size'],
    unchanged_boot_load_addresses_and_reservations=True,actual_Image_extent_smaller_and_no_overlap=True,
    original_virtual_delay_and_OOL_route=True,all_original_driver_operations_retained=True,
    RDMA_diagnostic_skip_preserved=True,charging_optin='unchanged ABSENT via byte-identical compiled/runtime DT',
    accepted_writer_barriers_and_mapping_unchanged=True,old_six_protocols_admitted=False,
    execute_Transport_Guard_and_adapters_byte_identical=True,adb_mode='0755',installer_changes=p['installer']['changes'],
    remote_py_sha256=sha(remote),local_patch_and_parser_match_parent_review=True,local_controls_rerun_on_resume=False)
(R/'evidence/preservation.json').write_text(json.dumps(preservation,indent=2)+'\n')
prepost=dict(base_remote=i['base_remote'],candidate_remote=i['remote_root'],changed_sources=read('source-pins.json'),
    source_and_output_freeze='base-freeze.json / repository-preservation.json',base_image_sha256=read('base-provenance-gate.json')['compiled_image_sha256'],
    new_image_sha256=p['compiled_Image_gz_dtb']['sha256'],expected_physical_preimage_full_p10=p['admitted_current_full_p10'],
    expected_candidate_full_p10=p['full_p10'],physical_preimage_supplied_not_freshly_observed=True)
(R/'evidence/prepost.json').write_text(json.dumps(prepost,indent=2)+'\n')
commands=dict(PLAN=f'python3 -B {R}/source/install.py',
    parent_one_trial_install=f'python3 -B {R}/source/install.py --execute',
    parser=f'python3 -B {R}/scripts/decode_sparse.py /absolute/parent-private/complete-console.txt > /absolute/parent-private/sparse-result.json',
    build=build['command'])
(R/'evidence/exact-commands.json').write_text(json.dumps(commands,indent=2)+'\n')
handoff=dict(status='DELIVERED_ONE_SPARSE_OBSERVER_LIVENESS_CANDIDATE_STOP',run_uuid=i['run_uuid'],
    candidate=p['candidate'],full_p10=p['full_p10'],expected_current_full_p10=p['admitted_current_full_p10'],
    current_pin_supplied_not_freshly_observed=True,base_remote=i['base_remote'],owned_remote=i['remote_root'],
    mode_contract=contract,config=p['config'],ramdisk=p['ramdisk'],helper=p['init'],helper_uuid=p['helper_uuid'],
    DT_compiled=p['compiled_DTB'],DT_runtime=p['runtime_DTB'],bootargs=p['bootargs'],initrd=p['initrd'],layout=p['layout'],
    System_map=read('System.map-uncompressed.json'),commands=commands,
    checks=dict(actual_base_caller='base-provenance-gate.json',source='source-checks.json',actual_ELF='linked-capture.json',
        proof='sparse-proof.md',prepost='prepost.json',preservation='preservation.json',packaging='packaging-receipt.json',
        isolated_PLAN='plan-isolation-receipt.json',original_local_controls='local-checks.json',kernel_compile_attempts=1,
        compiler_corrections=0,checker_corrections='checker-corrections.jsonl: memcpy alias only; no rebuild',
        local_controls_rerun_on_resume=False),
    VM=dict(project='PROJECT_REDACTED',zone='us-central1-a',instance='PROJECT_REDACTED',id=after['id'],
        final='TERMINATED',own_master_closed=True,remote_py_sha256=sha(remote)),
    preserved_history=dict(authentication_failure='before.stderr',blocked_handoff='handoff.auth-blocked.json',
        blocked_README='README.auth-blocked.md',identity_snapshot_state='identity.json state is the original pre-build snapshot, not current delivery status'),
    device_contacted=False,physical_trial_performed=False,physical_GO=False,full_OS_GO=False,
    parent_owns_one_physical_trial=True,standing_eventual_Power_fallback=True,
    limits=['Old six protocols deliberately absent; this is an alternate observation contract.',
        'Positive supports load/timing sensitivity, not exclusive cause or Android17 readiness.',
        'Early iteration-cap completion is valid progress, not failed timer or full bounded pass.',
        'Missing final is unresolved publication/environment, not instrumentation exoneration.',
        'Sparse accepted publication retains original PoC cleans and DSB SY and can still perturb execution.',
        'No private stock/root dependency-chain validation by isolated PLAN; all delivered guards remain intact.',
        '32.923s includes firmware and is not candidate uptime/counter calibration; cached DSB PC epoch unestablished.',
        'UNKNOWN STOP; consult Large before any new guess. No automatic retry/next unit/watchdog/CIRQ build/full OS GO.'])
(R/'evidence/handoff.json').write_text(json.dumps(handoff,indent=2)+'\n')
names=['candidate.img','candidate.p10.raw','Image.gz-dtb','resolved.config','System.map.gz','System.map','ramdisk.wrapped','runtime.dtb']
(R/'artifacts/SHA256SUMS').write_text(''.join(sha(R/'artifacts'/n)+'  '+n+'\n' for n in names))
print(json.dumps(dict(status=handoff['status'],candidate=p['candidate'],full_p10=p['full_p10'],UUID=i['run_uuid'],VM='TERMINATED',kernel_builds=1,isolated_PLAN_calls=1),indent=2))
