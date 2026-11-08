from pathlib import Path
import base64,json,remote
R=Path(__file__).resolve().parents[1]
files={str(p.relative_to(R)):base64.b64encode(p.read_bytes()).decode() for p in [R/'README.md',R/'HANDOFF.md',R/'evidence/inherited-validator-audit.json']}
s='FILES='+repr(files)+'\n'+r'''
from pathlib import Path
import os,resource,signal,base64,json,sys,ast,subprocess,datetime
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(180,180));signal.alarm(240)
R=Path('/srv/android/asus-reviewed-build-kit/r9-exec-r1');F=Path('/srv/android/asus-reviewed-build-kit/r9-exec-r1-fixtures');B=Path('/srv/android/asus-reviewed-build-kit/r9')
assert not (R/'inputs/kit-pins.json').exists() and not (R/'attempt').exists() and not (R/'parent-review').exists()
for rel,b in FILES.items():
 with (R/rel).open('xb') as f:f.write(base64.b64decode(b))
sys.path.insert(0,str(R/'scripts'))
from integrate import verify_pins,read,sha
from continuation import preservation,deltas
from artifact import REL,check_preimage,admit
plan=read(R/'inputs/plan.json');qa=read(R/'evidence/linux-qa.json');assert qa['script_sha256']=={p.name:sha(p) for p in (R/'scripts').iterdir() if p.is_file()};assert qa['tests_exit_code']==0 and 'Ran 54 tests' in qa['tests_tail'];assert qa['lineage']['outputs']==61 and qa['lineage']['prior_r8']==38 and qa['lineage']['qualified_bpf_baseline']==23
scope=read(R/'evidence/scope-preservation.json')
for path,row in scope['source_scope_pins'].items():assert sha(path)==row['sha256'] and Path(path).stat().st_size==row['bytes'],path
for path,row in scope['cache'].items():assert sha(path)==row['sha256'] and Path(path).stat().st_mtime_ns==row['mtime_ns'],path
for path,row in scope['images_metadata'].items():assert dict(bytes=Path(path).stat().st_size,mtime_ns=Path(path).stat().st_mtime_ns,inode=Path(path).stat().st_ino)==row
assert verify_pins(B)=='7850aa14d465cfa7cb061ed6cde5fe23c28041a5b4f5e9f7fd8c7d4d62956b5c';assert len(read(B/'inputs/kit-pins.json'))==184;preservation(plan);check_preimage(Path(plan['aosp'])/REL);admit(plan['artifact_staging']);deltas(plan)
expected_changed={'integrate.py','build.sh','cache_lineage.py','verify_product_r3.py','validate_completed_product.py','verify_root_payload.py'};expected_new={'native_state.py','graph_context.py','frozen_channel.py'}
actual_changed={p.name for p in (R/'scripts').iterdir() if p.is_file() and (B/'scripts'/p.name).is_file() and sha(p)!=sha(B/'scripts'/p.name)};actual_new={p.name for p in (R/'scripts').iterdir() if p.is_file() and not (B/'scripts'/p.name).exists()};assert actual_changed==expected_changed and actual_new==expected_new
assert sha(R/'scripts/verify_root_payload.py')=='c819e17595d14531d065fbafdab4a44871f34cfb7120490a75e488083e0e74f7'
for p in (R/'scripts').glob('*.py'):ast.parse(p.read_text(),filename=str(p))
assert subprocess.run(['bash','-n',str(R/'scripts/build.sh')]).returncode==0
assert sum(p.stat().st_size for p in R.rglob('*') if p.is_file())<256*1024**2
assert sum(p.stat().st_size for p in F.rglob('*') if p.is_file())<768*1024**2
pins={}
for folder in ['scripts','inputs','tests','evidence']:
 for p in sorted((R/folder).rglob('*')):
  if p.is_file() and p.name!='kit-pins.json' and '__pycache__' not in p.parts:
   assert not p.is_symlink();pins[str(p.relative_to(R))]=sha(p)
for name in ['README.md','HANDOFF.md']:pins[name]=sha(R/name)
with (R/'inputs/kit-pins.json').open('x') as f:json.dump(pins,f,indent=2,sort_keys=True);f.write('\n')
seal=verify_pins(R)
r=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='SEALED_PREPARATION_FOR_PARENT_KIT_REVIEW',kit=str(R),kit_pins_sha256=seal,pinned_files=len(pins),lineage_map_sha256=sha(plan['native_lineage_map']),bpf_matrix_sha256=sha(plan['qualified_baseline_map']),parent_method_sha256=sha(plan['native_cache_method']),parent_conditional_bpf_sha256=sha(plan['bpf_runtime_conditional_method']),prior_r8_execution_outputs=38,qualified_baseline_bpf_outputs=23,selected_bpf_objects=26,linux_tests_passed=54,source_delta_paths=[REL],artifact_path=plan['artifact_staging'],artifact_sha256='1d2f61832b2596b0046cb82cf3634609ea866098d097a83fac27c35272ac726a',artifact_bytes=260835655,parent_kit_approved=False,integration=False,native_build=False,revision='r9',runtime_bpf_acceptance_conditional=True,physical_go=False)
with (R/'kit-seal.json').open('x') as f:json.dump(r,f,indent=2,sort_keys=True);f.write('\n')
for rel in pins:(R/rel).chmod(0o444)
(R/'inputs/kit-pins.json').chmod(0o444);(R/'kit-seal.json').chmod(0o444)
assert verify_pins(R)==seal
print(json.dumps(dict(receipt=r,manifest=pins),indent=2))
'''
x=json.loads(remote.run(s));(R/'kit-seal.json').write_text(json.dumps(x['receipt'],indent=2,sort_keys=True)+'\n');(R/'inputs/kit-pins.json').write_text(json.dumps(x['manifest'],indent=2,sort_keys=True)+'\n');print(json.dumps(x['receipt'],indent=2))
