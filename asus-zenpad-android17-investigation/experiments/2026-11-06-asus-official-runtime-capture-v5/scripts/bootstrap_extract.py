import base64,json
from pathlib import Path
from remote import ROOT,run
files={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in ('inputs/v4-binding.json','scripts/extract_v4.py')}
script=r'''import base64,json,os,resource,subprocess
from pathlib import Path
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(30,30))
r=Path('/srv/android/asus-official-runtime-capture/preparation-v5');assert r.parent.resolve()==r.parent;r.mkdir(mode=0o700)
for d in ('inputs','scripts','evidence'):(r/d).mkdir(mode=0o700)
for n,b in json.loads(DATA).items():
 with (r/n).open('xb') as f:f.write(base64.b64decode(b))
p=subprocess.run(['python3','-B',str(r/'scripts/extract_v4.py')],capture_output=True,text=True,timeout=180)
if p.returncode:raise RuntimeError(p.stderr)
print(p.stdout)
'''.replace('DATA',repr(json.dumps(files)))
result=run(script)
with (ROOT/'evidence/v4-extracted-records.json').open('x') as f:f.write(json.dumps(json.loads(result),indent=2)+'\n')
d=json.loads(result);print(json.dumps({k:d[k] for k in ('record_count','record_bytes','elapsed_seconds','cpu_seconds','max_rss_KiB','index_identity_unchanged')}))
