from pathlib import Path
import json,remote
R=Path(__file__).resolve().parents[1]
s=r'''
from pathlib import Path
import os,resource,signal,json,sys,subprocess,datetime
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(180,180));signal.alarm(240)
R=Path('/srv/android/asus-reviewed-build-kit/r9-exec-r1');F=Path('/srv/android/asus-reviewed-build-kit/r9-exec-r1-fixtures');B=Path('/srv/android/asus-reviewed-build-kit/r9')
sys.path.insert(0,str(R/'scripts'))
from integrate import verify_pins,read,sha
from continuation import preservation
from artifact import REL,check_preimage,admit
seal=verify_pins(R);assert seal=='744fa117bba0e4ba9895af792ddc71f1cbe99196cb752593e560064ef8d41e69'
plan=read(R/'inputs/plan.json');scope=read(R/'evidence/scope-preservation.json')
p=subprocess.run([sys.executable,'-B',str(R/'scripts/integrate.py')],cwd=F,capture_output=True,text=True,timeout=60)
assert p.returncode==20 and json.loads(p.stdout)['error']=='Parent-authored r8 failure acceptance required',p.stdout+p.stderr
q=subprocess.run([sys.executable,'-B',str(R/'scripts/integrate.py'),'--audit-inputs'],cwd=F,capture_output=True,text=True,timeout=120)
assert q.returncode==0,q.stdout+q.stderr
audit=json.loads(q.stdout);assert audit['result']['lineage']['outputs']==61
for path,row in scope['source_scope_pins'].items():assert sha(path)==row['sha256']
for path,row in scope['cache'].items():assert sha(path)==row['sha256'] and Path(path).stat().st_mtime_ns==row['mtime_ns']
for path,row in scope['images_metadata'].items():assert dict(bytes=Path(path).stat().st_size,mtime_ns=Path(path).stat().st_mtime_ns,inode=Path(path).stat().st_ino)==row
assert verify_pins(B)=='7850aa14d465cfa7cb061ed6cde5fe23c28041a5b4f5e9f7fd8c7d4d62956b5c';preservation(plan);check_preimage(Path(plan['aosp'])/REL);admit(plan['artifact_staging'])
assert not (R/'attempt').exists() and not (R/'parent-review').exists();assert not list(Path(plan['logs']).glob('full-build-r9.*'))
assert all((R/rel).stat().st_mode&0o222==0 for rel in read(R/'inputs/kit-pins.json'))
r=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),kit_pins_sha256=seal,pinned_files=193,pinned_files_readonly=True,default_plan_exit=p.returncode,default_plan=json.loads(p.stdout),audit_inputs_exit=q.returncode,audit_inputs=audit,source_cache_r8_and_old_r9_preserved=True,images_metadata_unchanged=True,active_webview_original_pointer=True,new_r9_attempt_absent=True,parent_review_absent=True,native_r9_logs_absent=True,integration=False,native_launch=False,physical_go=False)
with (F/'post-seal-verification.json').open('x') as f:json.dump(r,f,indent=2);f.write('\n')
assert verify_pins(R)==seal
print(json.dumps(r,indent=2))
'''
r=remote.run(s);(R/'evidence/post-seal-verification.json').write_text(r);print(r)
