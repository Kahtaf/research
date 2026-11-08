"""Seal only v5 after exact final Linux/projection qualification; no large rehash."""
import hashlib,json,os,resource,stat,subprocess,sys,time
from pathlib import Path
ROOT=Path('/srv/android/asus-official-runtime-capture/preparation-v5')
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(60,60));resource.setrlimit(resource.RLIMIT_FSIZE,(64*1024**2,64*1024**2))
start=time.monotonic();assert ROOT.resolve()==ROOT and not (ROOT/'FINALIZED.json').exists()
def sha_file(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for block in iter(lambda:f.read(1024**2),b''):h.update(block)
 return h.hexdigest()
pins=json.loads((ROOT/'tool-pins.json').read_bytes());seal=sha_file(ROOT/'tool-pins.json');handoff=json.loads((ROOT/'HANDOFF.json').read_bytes())
assert handoff['tool_seal_sha256']==seal
for name,digest in pins.items():assert sha_file(ROOT/name)==digest,name
qa=json.loads((ROOT/'evidence/qa-qualified-execution.json').read_bytes());tests=json.loads((ROOT/'evidence/qa-qualified.json').read_bytes())
assert qa['returncode']==0 and not qa['changed_during_tests'] and qa['tested_pins']==pins
assert tests['tests_run']>=115 and not tests['failures'] and not tests['errors'] and tests['cpu_count']==1 and tests['address_space_limit_bytes']==1024**3
projection=json.loads((ROOT/'evidence/projection-qualified.json').read_bytes())
assert projection['scope_replay_complete'] and projection['status']=='PROJECTION_PASS' and projection['mandatory_target_count']==projection['mandatory_direct_resolved']==25 and not projection['mandatory_root_refusals'] and not projection['ancestor_refusals'] and not projection['metadata_fixed_role_refusals']
for name,digest in projection['tested_pins'].items():assert pins['source/'+name]==digest,name
sys.path[:0]=[str(ROOT/'source'),str(ROOT/'scripts')]
from v4_fixture import V4Fixture
fixture=V4Fixture(ROOT);fixture.recheck();index_identity=fixture.before;fixture.close()
oldpins_path=ROOT.parent/'preparation-v4/tool-pins.json'
assert sha_file(oldpins_path)=='bb23b4634369750f54059becaa9d96c3ec3a607c8e88ebb273b964255faf155b'
oldpins=json.loads(oldpins_path.read_bytes())
protected=('source/gates.py','source/safeio.py','source/elf.py','source/packages.py','inputs/profile-r8.json','tests/test_capture.py')
for name in protected:assert pins[name]==oldpins[name],name
manifest={};storage=0
for path in sorted(ROOT.rglob('*')):
 if path.is_dir():continue
 assert stat.S_ISREG(path.lstat().st_mode) and not path.is_symlink()
 size=path.stat().st_size;assert size<=64*1024**2
 storage+=size;assert storage<=512*1024**2
 manifest[str(path.relative_to(ROOT))]={'bytes':size,'sha256':sha_file(path)}
source_evidence=json.loads((ROOT/'inputs/public-source-evidence.json').read_bytes())
for name,pin in source_evidence['files'].items():assert sha_file(ROOT/'evidence/public-source'/name)==pin['sha256']
p=subprocess.run(['python3','-B',str(ROOT/'source/capture.py')],capture_output=True,text=True,check=True,timeout=10)
plan=json.loads(p.stdout);assert plan['mode']=='PLAN_ONLY' and not plan['source_or_output_inspected'] and not plan['lock_acquired'] and plan['profile']['revision']=='r8'
usage=resource.getrusage(resource.RUSAGE_SELF)
r={'schema':1,'status':'SEALED_PREPARATION_GRAPH_PROJECTION_ONLY','preparation':str(ROOT),'tool_seal_sha256':seal,'all_final_tool_pins_match':True,'exact_final_linux_candidate':True,'linux_tests_passed':tests['tests_run'],'mandatory_producers_resolved':25,'mandatory_refusals':{},'index_identity_unchanged':True,'v4_index_identity':index_identity,'v4_index_sha256_inherited_from_seal':fixture.binding['index_sha256'],'old_graphs_or_index_fully_rehashed':False,'new_large_index_allocated':False,'protected_v4_files_equal':list(protected),'owned_storage_bytes':storage,'owned_storage_hard_ceiling_bytes':512*1024**2,'owned_files':manifest,'static_plan_only_executed':True,'actual_output_select_verify_copy_executed':False,'actual_payload_reads':False,'r9_profile_created':False,'full_capture_PASS':False,'runtime_ready':False,'physical_GO':False,'cpu_count':1,'address_space_limit_bytes':1024**3,'cpu_seconds_limit':60,'elapsed_seconds':round(time.monotonic()-start,3),'cpu_seconds':round(usage.ru_utime+usage.ru_stime,3),'max_rss_KiB':usage.ru_maxrss}
with (ROOT/'FINALIZED.json').open('x') as f:json.dump(r,f,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in r.items() if k!='owned_files'}))
