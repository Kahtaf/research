"""Fetch only bounded own-v6 receipts; no old graph, kit or source reads."""
import base64,json
from remote import ROOT,run
script=r'''import base64,json,os,resource
from pathlib import Path
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(30,30))
r=Path('/srv/android/asus-official-runtime-capture/preparation-v6/evidence');data={};total=0
for p in sorted(r.glob('*')):
 if p.is_file():
  assert not p.is_symlink() and p.stat().st_size<=48*1024**2;total+=p.stat().st_size;assert total<=32*1024**2
  data[p.name]=base64.b64encode(p.read_bytes()).decode()
print(json.dumps(data))
'''
files=json.loads(run(script))
for name,b in files.items():
 data=base64.b64decode(b);p=ROOT/'evidence'/name
 if p.exists():assert p.read_bytes()==data,name
 else:
  with p.open('xb') as f:f.write(data)
print(json.dumps({'files':len(files),'bytes':sum(len(base64.b64decode(b)) for b in files.values())}))
