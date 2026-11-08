"""Finalize only the owned v6 preparation after exact tested-runtime equivalence."""
import hashlib,json,os,resource,subprocess,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[1]
assert R==Path('/srv/android/asus-official-runtime-capture/preparation-v6') and R.resolve()==R
assert not (R/'FINALIZED.json').exists()
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(60,60));resource.setrlimit(resource.RLIMIT_FSIZE,(48*1024**2,48*1024**2))
def sha(p):
 assert p.is_file() and not p.is_symlink() and p.stat().st_size<=48*1024**2
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024**2),b''):h.update(b)
 return h.hexdigest()
def load(n):return json.loads((R/n).read_bytes())
def put(n,obj):
 with (R/n).open('x') as f:json.dump(obj,f,indent=2);f.write('\n')
def size():
 total=0
 for p in R.rglob('*'):
  assert not p.is_symlink()
  if p.is_file():total+=p.stat().st_size
 assert total<=128*1024**2
 return total
start=time.monotonic();before=size();pins=load('tool-pins.json');assert len(pins)<=256
assert all(sha(R/n)==h for n,h in pins.items())
runtime=load('runtime-pins.json');accepted=['baseline-001','effective-001','review23-001','duplicate-before-002','duplicate-after-001'];results={}
for label in accepted:
 receipt=load('evidence/'+label+'-execution.json');assert receipt['success'] and not receipt['changed_during_phase']
 assert all(receipt['tested_pins'].get(n)==h==sha(R/n) for n,h in runtime.items()),label
 assert receipt['cpu_count']==1 and receipt['address_space_limit_bytes']==1024**3 and receipt['child_cpu_limit_seconds']==120
 assert not receipt['timeout_fired'] and not receipt['process_signals_sent']
 results[label]={k:receipt[k] for k in ('returncode','elapsed_seconds','child_cpu_seconds','max_child_rss_KiB')}
# Runtime/test adapters are included in runtime-pins. Runner correction applies
# after the first three self-limited children; corrected duplicate pair binds it.
for label in accepted[-2:]:assert load('evidence/'+label+'-execution.json')['tested_pins']['scripts/run_phase.py']==sha(R/'scripts/run_phase.py')
assert load('evidence/baseline-001-tests.json')['tests_run']==115
assert load('evidence/effective-001-tests.json')['tests_run']==35
assert load('evidence/review23-001-cases.json')['expectations_met']==23
assert load('evidence/duplicate-after-001-execution.json')['cases']['all_pass']
assert [x['pass'] for x in load('evidence/duplicate-before-002-execution.json')['cases']['cases']]==[True,False,False,True]
assert sha(R/'source/graph.py')==load('inputs/parent-duplicate/source-pins.json')['postimage_sha256']
assert sha(R/'inputs/qualified-host-metadata-tools.json')=='624ff875e00eea2489502489bfad4587efa398457d110bf404baac76e97aeff3'
def bounds():resource.setrlimit(resource.RLIMIT_CPU,(30,30))
plan=subprocess.run([sys.executable,'-B',str(R/'source/capture.py'),'plan','--mode','PLAN_ONLY'],capture_output=True,text=True,cwd=R,timeout=30,preexec_fn=bounds,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
assert plan.returncode==0 and not plan.stderr
p=json.loads(plan.stdout);assert p['mode']=='PLAN_ONLY' and not p['source_or_output_inspected'] and not p['lock_acquired'] and not p['runtime_ready'] and not p['physical_GO']
put('evidence/final-default-plan.json',{'returncode':0,'stdout_sha256':hashlib.sha256(plan.stdout.encode()).hexdigest(),'stdout_bytes':len(plan.stdout.encode()),'source_or_output_inspected':False,'lock_acquired':False,'cpu_limit_seconds':30,'wall_timeout_seconds':30})
assert all(sha(R/n)==h for n,h in pins.items())
seal=sha(R/'tool-pins.json')
receipt={'status':'FINAL_RUNTIME_EQUALS_TESTED_BYTES','tool_seal_sha256':seal,'runtime_pin_count':len(runtime),'accepted_phases':results,'all_phase_runtime_pins_equal_final':True,'production_sources_changed_after_QA':False,'historical_limit_correction':'duplicate-before-001-bound-correction.json','owned_bytes_before':before,'owned_bytes_before_handoff':size(),'allocation_ceiling_bytes':128*1024**2,'cpu_count':1,'address_space_ceiling_bytes':1024**3,'finalizer_cpu_ceiling_seconds':60,'finalizer_elapsed_seconds':round(time.monotonic()-start,3),'actual_state_read':False,'native_engine_executed':False,'real_graph_requalified':False,'independent_review':'pending'}
put('evidence/finalization.json',receipt)
put('HANDOFF.json',{'schema':1,'status':'FIXTURE_QUALIFIED_INDEPENDENT_REVIEW_PENDING','preparation':str(R),'tool_seal_sha256':seal,'tool_pin_count':len(pins),'upstream_ninja_commit':load('inputs/ninja-1.12.1-pins.json')['commit'],'parent_graph_postimage_sha256':sha(R/'source/graph.py'),'profile_sha256':sha(R/'inputs/profile-r8.json'),'selector_sha256':sha(R/'inputs/selector.json'),'metadata_tool_group_sha256':sha(R/'inputs/qualified-host-metadata-tools.json'),'runtime_pins_sha256':sha(R/'runtime-pins.json'),'minimal_diff_sha256':sha(R/'minimal-v5-v6.patch'),'review_packet':'REVIEW-PACKET.md','resource_and_equivalence_receipt_sha256':sha(R/'evidence/finalization.json'),'default_plan_receipt_sha256':sha(R/'evidence/final-default-plan.json'),'baseline_tests':115,'new_tests':35,'review_cases':23,'parent_duplicate_cases':4,'prior_v5_seal':load('evidence/static-preservation.json')['v5_tool_seal_sha256'],'actual_capture':False,'actual_graph_scan':False,'actual_R9_profile':False,'metadata_query_or_admission':False,'runtime_ready':False,'physical_GO':False})
put('FINALIZED.json',{'schema':1,'tool_seal_sha256':seal,'handoff_sha256':sha(R/'HANDOFF.json'),'policy':'immutable sibling; additions or corrections require new preparation','owned_bytes_before_marker':size()})
retained=size()
for p in R.rglob('*'):
 if p.is_file():p.chmod(0o444)
for p in sorted((p for p in R.rglob('*') if p.is_dir()),key=lambda p:len(p.parts),reverse=True):p.chmod(0o555)
R.chmod(0o555)
print(json.dumps({'seal':seal,'retained_bytes':retained,'pin_count':len(pins),'finalized':True}))
