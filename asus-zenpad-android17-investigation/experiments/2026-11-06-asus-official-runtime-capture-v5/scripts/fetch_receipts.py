"""Transfer only bounded v5 receipts/public-source snapshots, never large v4 files."""
import base64,json
from remote import ROOT,run
script=r'''import base64,json,os,resource
from pathlib import Path
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(30,30))
r=Path('/srv/android/asus-official-runtime-capture/preparation-v5/evidence');files={};total=0
for p in sorted(r.rglob('*')):
 if p.is_file():
  assert not p.is_symlink() and p.stat().st_size<=64*1024**2;total+=p.stat().st_size;assert total<=64*1024**2
  files[str(p.relative_to(r))]=base64.b64encode(p.read_bytes()).decode()
print(json.dumps(files))
'''
files=json.loads(run(script))
for n,b in files.items():
 p=ROOT/'evidence'/n;data=base64.b64decode(b);p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():
  if p.read_bytes()!=data:raise RuntimeError('preserve differing receipt: '+n)
 else:
  with p.open('xb') as f:f.write(data)
print(json.dumps({'files':len(files),'bytes':sum(len(base64.b64decode(v)) for v in files.values())}))
