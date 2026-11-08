exec(open('2026-11-06-asus-r8-continuation-kit/preparation/inspect_remote.py').read().split('script=r')[0])
r=m.run(r'''
from pathlib import Path
import sys,json,os,resource
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
R=Path('/srv/android/asus-reviewed-build-kit/r8');sys.path.insert(0,str(R/'scripts'))
from integrate import verify_pins,read,audit_inputs,write
result=dict(seal=verify_pins(R),audit=audit_inputs(read(R/'inputs/plan.json')),read_only=True,global_lock_acquired=False,product_build_started=False)
write(R/'evidence/source-audit-final.json',result);print(json.dumps(result,indent=2))
''');Path('2026-11-06-asus-r8-continuation-kit/evidence/source-audit-final.json').write_text(r);print(r)
