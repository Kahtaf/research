from pathlib import Path
import json,base64,remote
R=Path(__file__).resolve().parents[1]
files={str(p.relative_to(R)):base64.b64encode(p.read_bytes()).decode() for p in [R/'inputs/prior-source-scope-pins.json',R/'inputs/prior-final-source-audit.json',R/'inputs/prior-selected-lfs-product-audit.json',R/'inputs/UNAPPROVED-prior-review-schema.json']}
s='FILES='+repr(files)+'\n'+r'''
from pathlib import Path
import os,resource,signal,base64,json,sys,datetime
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(180,180));signal.alarm(240)
R=Path('/srv/android/asus-reviewed-build-kit/r9-exec-r1');B=Path('/srv/android/asus-reviewed-build-kit/r9');A=Path('/srv/android/lineage24');M=Path('/srv/android/asus-reviewed-build-kit/r9-webview-input-milestone-v1')
for rel,b in FILES.items():
 p=R/rel
 with p.open('xb') as f:f.write(base64.b64decode(b))
sys.path.insert(0,str(R/'scripts'))
from integrate import verify_pins,read,sha
from continuation import preservation,deltas
from artifact import REL,check_preimage,admit
plan=read(R/'inputs/plan.json');assert verify_pins(B)=='7850aa14d465cfa7cb061ed6cde5fe23c28041a5b4f5e9f7fd8c7d4d62956b5c';assert len(read(B/'inputs/kit-pins.json'))==184
assert verify_pins(Path(plan['r8_kit']))=='f55aedf8ac9d2a513e3663230db0b9d802e72b5df512fc0db6b3714331a7efa4';preservation(plan)
scoped=read(R/'inputs/prior-source-scope-pins.json')
for path,row in scoped.items():assert sha(path)==row['sha256'] and Path(path).stat().st_size==row['bytes'],path
cache={}
for name,want in [('.siso_fs_state','1715cf4cd15d2c2a076ff16ce0a28abbaf598680840de91e241924f27cf367a3'),('.siso_deps','3594b00fbf8c55ed8b1cb9f67f33263f0dfd5ed333442069ef3a3f01419505b5')]:
 p=A/'out'/name;assert sha(p)==want;cache[str(p)]=dict(sha256=want,bytes=p.stat().st_size,mtime_ns=p.stat().st_mtime_ns)
assert sha(M/'pins.json')=='3e6ca30a3074cdd7f19dd522111c52fadbfdb311a3aa16fd23563c9011e35437'
for rel,row in read(M/'pins.json').items():assert sha(M/rel)==(row if isinstance(row,str) else row['sha256'])
check_preimage(A/REL);admit(plan['artifact_staging']);assert not (R/'attempt').exists() and not (R/'parent-review').exists()
images={str(p):dict(bytes=p.stat().st_size,mtime_ns=p.stat().st_mtime_ns,inode=p.stat().st_ino) for p in Path(plan['product_out']).glob('*.img')}
r=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),blocked_r9_seal=sha(B/'inputs/kit-pins.json'),blocked_r9_files_verified=184,r8_attempt_and_logs_preserved=True,milestone_pins_sha256=sha(M/'pins.json'),payload=admit(plan['artifact_staging']),active_preimage_original_pointer=True,source_scope_pins=scoped,cache=cache,images_metadata=images,source_delta=deltas(plan),prior_complete_audit_pin=sha(R/'inputs/prior-final-source-audit.json'),new_full_tree_scan=False,no_native_or_source_operations=True,physical_go=False)
with (R/'evidence/scope-preservation.json').open('x') as f:json.dump(r,f,indent=2);f.write('\n')
print(json.dumps(r,indent=2))
'''
r=remote.run(s);(R/'evidence/scope-preservation.json').write_text(r);print('Preservation receipt recorded')
