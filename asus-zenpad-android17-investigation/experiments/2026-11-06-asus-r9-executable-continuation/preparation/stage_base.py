from pathlib import Path
import json,base64,remote
R=Path(__file__).resolve().parents[1]
files={str(p.relative_to(R)):base64.b64encode(p.read_bytes()).decode() for p in (R/'inputs').rglob('*') if p.is_file()}
s='FILES='+repr(files)+'\n'+r'''
from pathlib import Path
import shutil,json,base64,hashlib,os,resource,signal,re
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(120,120));signal.alarm(180)
R=Path('/srv/android/asus-reviewed-build-kit/r9-exec-r1');O=Path('/srv/android/asus-reviewed-build-kit/r9');A=Path('/srv/android/lineage24')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
pins=json.loads((O/'inputs/kit-pins.json').read_text());assert sha(O/'inputs/kit-pins.json')=='7850aa14d465cfa7cb061ed6cde5fe23c28041a5b4f5e9f7fd8c7d4d62956b5c'
for rel,h in pins.items():assert sha(O/rel)==h
for p in (O/'inputs').iterdir():
 if p.name=='kit-pins.json':continue
 dst=R/'inputs'/p.name
 if p.is_dir():shutil.copytree(p,dst)
 else:shutil.copyfile(p,dst)
for p in (R/'inputs').rglob('*'):
 if p.is_file():p.chmod(0o644)
for rel,b in FILES.items():
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(base64.b64decode(b))
plan=json.loads((R/'inputs/plan.json').read_text());plan.update(run_root=str(R),native_cache_method=str(R/'inputs/parent-native-cache-method-acceptance.json'),native_lineage_map=str(R/'inputs/native-lineage-map.json'),qualified_baseline_method=str(R/'inputs/parent-bpf-qualified-baseline-classification.json'),qualified_baseline_map=str(R/'inputs/bpf-classification.json'),parent_contract='Controlled native incremental trust; explicit per-output R8/current execution plus exact qualified BPF baseline; parent-only r8 acceptance and one-shot r9; WebView-only source delta')
# Own copies for all paths previously inside the blocked kit. Immutable external staging remains unchanged.
plan=json.loads(json.dumps(plan).replace(str(O)+'/inputs/',str(R)+'/inputs/'))
(R/'inputs/plan.json').write_text(json.dumps(plan,indent=2,sort_keys=True)+'\n')
r=dict(blocked_r9_seal=sha(O/'inputs/kit-pins.json'),blocked_r9_files_verified=len(pins),method_sha256=sha(R/'inputs/parent-native-cache-method-acceptance.json'),new_kit=str(R),active_source_changed=False)
for rel in ['build/blueprint/context.go','build/blueprint/ninja_writer.go']:
 p=A/rel
 if p.is_file():
  lines=p.read_text().splitlines();r[rel]=[dict(line=i+1,text=l) for i,l in enumerate(lines) if any(s in l.lower() for s in ['shard','filebucket','fnv','ninjafilesshards','ninjafilewriters'])][:80]
with (R/'evidence/base-preservation.json').open('x') as f:json.dump(r,f,indent=2);f.write('\n')
print(json.dumps(r,indent=2))
'''
r=remote.run(s);(R/'evidence/base-preservation.json').write_text(r);print(r)
