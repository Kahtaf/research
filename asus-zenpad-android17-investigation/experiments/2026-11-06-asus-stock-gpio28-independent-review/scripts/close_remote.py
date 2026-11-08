from pathlib import Path
import os,resource,signal,json,hashlib
resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(90,90));signal.alarm(180);os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
R=Path('/srv/android/asus-stock-gpio28-review-20261106-r1');E=R/'evidence';B=Path('/srv/android/asus-bmc156-full-kernel-r1')
assert not (E/'review-disposition.json').exists()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for name in ['lifetime-null','lifetime-routing-pm']:
 assert json.loads((E/(name+'-run.json')).read_text())['exit']==1
 assert 'runtime error: member access within null pointer' in (E/(name+'-run.log')).read_text()
assert json.loads((E/'lifetime-stale-suspend-run.json').read_text())['exit']==0
manifest=json.loads((E/'baseline-source-manifest.json').read_text());assert all(sha(B/'kernel'/n)==h for n,h in manifest.items())
post=json.loads((E/'candidate-source-manifest.json').read_text());assert all(sha(R/'kernel'/n)==h for n,h in post.items())
assert sha(B/'out/.config')=='10b212cabd28aad012582e86c64695ccd450650b4e09ec8da30c21e094f377c2'
assert sha(B/'out/arch/arm64/boot/Image.gz-dtb')=='e9cde06e85e752aec0433ea37fa926c31b4f7a72cd55453762ec6870e5bb5bf1'
size=sum(p.stat().st_size for p in R.rglob('*') if p.is_file());blocks=sum(p.stat().st_blocks*512 for p in R.rglob('*') if p.is_file());assert max(size,blocks)<4*1024**3
r=dict(disposition='CHANGES_REQUESTED_LIFETIME_BLOCKER',target_compilation_finished_before_blocker_identified=True,further_target_compiles_after_blocker=0,source_fixes=0,original_and_candidate_sources_unchanged=True,original_image_and_config_unchanged=True,owned_logical_bytes=size,owned_allocated_file_bytes=blocks,host_original='PASS 38 cases 984 assertions',host_extended='PASS 55 cases 23438 assertions (schedule-dependent assertion count)',fault_boundary='PASS 6 swallowed regmap errors demonstrated',negative_repros={'PM_after_detach':'UBSan expected exit 1','actual_routing_PM_after_detach':'UBSan expected exit 1','stale_suspend_on_reprobe':'On accepted; defect reproduced'},no_full_kernel_or_hardware_or_flash_GO=True)
(E/'review-disposition.json').write_text(json.dumps(r,indent=2)+'\n')
(R/'README.md').write_text('CHANGES REQUESTED: GPIO28 independent review. Real isolated ARM64 codec/GPIO/AFE objects and board DTB compiled before discovery of a blocking codec-private-data lifetime bug. No further target compilation. Evidence/lifetime-routing-pm-run.log reproduces actual routing PM callback null dereference after codec detach; lifetime-stale-suspend-run.log reproduces stale suspend state. No source fix, full kernel, hardware, integration, HAL qualification or flash GO. Own prefix only. All original BMC sources/image/config preserved. Read evidence/review-disposition.json and local review handoff before continuation. Preserve all failed attempts; do not rerun initialization.\n')
print(json.dumps(r,indent=2))
