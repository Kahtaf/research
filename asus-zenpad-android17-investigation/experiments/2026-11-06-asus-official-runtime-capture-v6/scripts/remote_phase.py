"""Deploy only own small v6 candidate, then one bounded serial fixture phase."""
import base64,json,sys
from remote import ROOT,run
phase,label=sys.argv[1:];assert phase in ('baseline','effective','review23','duplicate-before','duplicate-after');assert label.replace('-','').isalnum()
files={}
for folder in ('source','tests','inputs','scripts'):
 for p in sorted((ROOT/folder).rglob('*')):
  if p.is_file() and 'tmp' not in p.relative_to(ROOT).parts and '__pycache__' not in p.parts:files[str(p.relative_to(ROOT))]=base64.b64encode(p.read_bytes()).decode()
for name in ('README.md','REPORT.md','REVIEW-PACKET.md','METADATA-SOURCE-CONTRACT.md','manifest.schema.json','host-metadata-source-plan.schema.json','tool-pins.json'):
 if (ROOT/name).exists():files[name]=base64.b64encode((ROOT/name).read_bytes()).decode()
script=r'''import base64,json,os,resource,subprocess
from pathlib import Path
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(300,300));resource.setrlimit(resource.RLIMIT_FSIZE,(48*1024**2,48*1024**2))
r=Path('/srv/android/asus-official-runtime-capture/preparation-v6');assert r.parent.resolve()==r.parent
if not r.exists():r.mkdir(mode=0o700)
assert r.resolve()==r and not (r/'FINALIZED.json').exists()
(r/'evidence').mkdir(exist_ok=True)
for n,b in json.loads(FILES_PAYLOAD).items():
 assert '..' not in Path(n).parts and not Path(n).is_absolute()
 p=r/n;assert not p.is_symlink();p.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
 with p.open('wb') as f:f.write(base64.b64decode(b))
assert sum(p.lstat().st_size for p in r.rglob('*') if p.is_file() and not p.is_symlink())<=128*1024**2
p=subprocess.run(['python3','-B',str(r/'scripts/run_phase.py'),PHASE_ARG,LABEL_ARG],cwd=r,capture_output=True,text=True,timeout=190)
print(json.dumps({'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr}))
'''.replace('FILES_PAYLOAD',repr(json.dumps(files))).replace('PHASE_ARG',repr(phase)).replace('LABEL_ARG',repr(label))
r=json.loads(run(script));print(r['stdout'][-10000:]);print(r['stderr'][-3000:]);raise SystemExit(r['returncode'])
