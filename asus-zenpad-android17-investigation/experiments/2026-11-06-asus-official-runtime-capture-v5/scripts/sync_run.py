"""Small-file updates in unsealed owned v5 only; serial bounded script execution."""
import base64,json,sys
from remote import ROOT,run
name=sys.argv[1]
label=sys.argv[2] if len(sys.argv)>2 else None
assert label is None or label.replace('-','').isalnum()
assert name in ('extract_v4.py','qualify_projection.py','run_linux.py','collect_sources.py','extract_bindings.py','finalize.py')
files={}
for folder in ('source','inputs','tests','scripts'):
 for p in sorted((ROOT/folder).rglob('*')):
  if p.is_file() and 'tmp' not in p.relative_to(ROOT).parts and '__pycache__' not in p.parts:
   files[str(p.relative_to(ROOT))]=base64.b64encode(p.read_bytes()).decode()
for n in ('README.md','REPORT.md','METADATA-SOURCE-CONTRACT.md','host-metadata-source-plan.schema.json','manifest.schema.json','tool-pins.json','HANDOFF.json'):
 if (ROOT/n).exists():files[n]=base64.b64encode((ROOT/n).read_bytes()).decode()
script=r'''import base64,json,os,resource,subprocess
from pathlib import Path
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(300,300))
r=Path('/srv/android/asus-official-runtime-capture/preparation-v5');assert r.resolve()==r and r.is_dir() and not (r/'FINALIZED.json').exists()
for n,b in json.loads(DATA).items():
 p=r/n;assert not p.is_symlink();p.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
 with p.open('wb') as f:f.write(base64.b64decode(b))
assert sum(p.stat().st_size for p in r.rglob('*') if p.is_file())<=512*1024**2
env=dict(os.environ)
if RUN_LABEL_VALUE:
 env['V5_PROJECTION_LABEL']=RUN_LABEL_VALUE;env['V5_RUN_LABEL']=RUN_LABEL_VALUE
p=subprocess.run(['python3','-B',str(r/'scripts'/NAME)],capture_output=True,text=True,timeout=240,env=env)
print(json.dumps({'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr}))
'''.replace('DATA',repr(json.dumps(files))).replace('NAME',repr(name)).replace('RUN_LABEL_VALUE',repr(label))
result=json.loads(run(script))
if name=='extract_v4.py' and result['returncode']==0:
 data=json.loads(result['stdout']);(ROOT/'evidence/v4-extracted-records.json').write_text(json.dumps(data,indent=2)+'\n');print(json.dumps({k:data[k] for k in ('record_count','record_bytes','elapsed_seconds','cpu_seconds','max_rss_KiB','index_identity_unchanged')}))
else:print(result['stdout'][-15000:]);print(result['stderr'][-5000:])
if result['returncode']:raise SystemExit(result['returncode'])
