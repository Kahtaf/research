"""Preserve the failed single transport dispatch; never retry or claim a package."""
from pathlib import Path
import hashlib,json,stat
R=Path(__file__).resolve().parents[1];W=R.parent
load=lambda n:json.loads((R/'evidence'/n).read_text())
sha=lambda x:hashlib.sha256(x).hexdigest()
vm=load('vm-lifecycle.json');scope=load('source-scope-receipt.json');pins=load('original-public-pins.json')
assert vm['final_status']=='TERMINATED' and not vm.get('compile_and_small_fetch_completed',False)
assert 'ssh: connect to host IP_REDACTED port 22: Operation timed out' in (R/'evidence/compile-local.stderr.log').read_text()
assert not list((R/'artifacts').iterdir())
assert not (R/'evidence/compiler-receipt.json').exists() and not (R/'evidence/package-attempt.json').exists() and not (R/'evidence/install-plan.json').exists()
assert sha((R/'source/init.c').read_bytes())==scope['source_sha256']
for path,pin in pins.items():
 p=W/path
 assert sha(p.read_bytes())==pin['sha256'] and p.stat().st_size==pin['bytes'] and oct(stat.S_IMODE(p.stat().st_mode))==pin['mode'],path
B=W/'2026-11-07-asus-linux49-runnable-timer-format-fix'
for n in ['install.py','bootformat.py','fdt.py','adb','legacy_adb.py']:assert (R/'source'/n).read_bytes()==(B/'source'/n).read_bytes()
assert stat.S_IMODE((R/'source/adb').stat().st_mode)==0o755
(R/'source/install.diff').write_text('')
(R/'evidence/installer-status.json').write_text(json.dumps(dict(status='UNMODIFIED_BASE_COPY_NOT_A_NEW_CANDIDATE_INSTALLER',candidate_hashes_unavailable=True,diff_empty=True,execute_Transport_Guard_and_entire_installer_byte_identical=True,adapters_copy2_byte_identical=True,adb_mode='0755',command_not_ready=True),indent=2)+'\n')
(R/'evidence/original-preservation.json').write_text(json.dumps(dict(public_original_files_checked=len(pins),all_unchanged=True,private_paths_read=False),indent=2)+'\n')
status=dict(status='STOPPED_COMPILE_SSH_CONNECT_TIMEOUT_NO_CANDIDATE',pid1_run_uuid=load('identity.json')['pid1_run_uuid'],source_scope='PASS',production_parser_cases=1,production_parser_check='PASS',kernel_base_check='PASS',helper_compile_transport_dispatches=1,remote_helper_compiler_invocations=0,compiler_not_started_reason='SSH TCP connection timed out before remote script execution',compiler_receipt_fetched=False,packaged_candidates=0,static_ELF_checks=0,default_PLAN_calls=0,no_automatic_retry=True,VM_id=vm['id'],VM_status=vm['final_status'],VM_start_stop_cycles=1,SSH_readiness_probes=vm['ssh_readiness_attempts'],SSH_readiness_elapsed_seconds=vm['readiness_elapsed_seconds'],device_or_ADB_commands=False,private_factory_or_raw_kernel_logs_accessed=False,kernel_or_product_work=False,new_cloud_resources=False,resource_caps_changed=False,physical_result='NOT_OBSERVED',saved_PL_reset32_meaning='UNKNOWN',next_userspace_variant_prepared=False)
(R/'evidence/final-status.json').write_text(json.dumps(status,indent=2)+'\n')
paths=[R/'README.md',*sorted((R/'source').glob('*')),*sorted((R/'scripts').glob('*.py')),*sorted((R/'artifacts').glob('*')),*sorted((R/'evidence').rglob('*'))]
(R/'SHA256SUMS').write_text(''.join(sha(f.read_bytes())+'  '+str(f.relative_to(R))+'\n' for f in paths if f.is_file()))
print(json.dumps(status,indent=2))
