"""Upload only own small final review files and freeze the existing v6 candidate."""
import base64,json
from remote import ROOT,run
files={}
for folder in ('source','tests','inputs','scripts','evidence'):
 for p in sorted((ROOT/folder).rglob('*')):
  if p.is_file() and 'tmp' not in p.relative_to(ROOT).parts and '__pycache__' not in p.parts:files[str(p.relative_to(ROOT))]=base64.b64encode(p.read_bytes()).decode()
for p in ROOT.glob('*'):
 if p.is_file():files[p.name]=base64.b64encode(p.read_bytes()).decode()
assert sum(len(base64.b64decode(x)) for x in files.values())<16*1024**2
script=r'''import base64,json,os,resource,subprocess
from pathlib import Path
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(90,90));resource.setrlimit(resource.RLIMIT_FSIZE,(48*1024**2,48*1024**2))
r=Path('/srv/android/asus-official-runtime-capture/preparation-v6');assert r.resolve()==r and not (r/'FINALIZED.json').exists()
for n,b in json.loads(PAYLOAD).items():
 assert not Path(n).is_absolute() and '..' not in Path(n).parts
 p=r/n;assert not p.is_symlink();p.parent.mkdir(parents=True,exist_ok=True);data=base64.b64decode(b)
 if p.exists() and (n.startswith('source/') or n.startswith('tests/') or n.startswith('evidence/')):assert p.read_bytes()==data,n
 else:p.write_bytes(data)
p=subprocess.run(['python3','-B',str(r/'scripts/finalize.py')],capture_output=True,text=True,cwd=r,timeout=75)
assert p.returncode==0,(p.stdout,p.stderr)
print(json.dumps({'result':json.loads(p.stdout),'files':{n:base64.b64encode((r/n).read_bytes()).decode() for n in ('HANDOFF.json','FINALIZED.json','evidence/finalization.json','evidence/final-default-plan.json')}}))
'''.replace('PAYLOAD',repr(json.dumps(files)))
result=json.loads(run(script))
for n,b in result['files'].items():
 with (ROOT/n).open('xb') as f:f.write(base64.b64decode(b))
print(json.dumps(result['result']))
