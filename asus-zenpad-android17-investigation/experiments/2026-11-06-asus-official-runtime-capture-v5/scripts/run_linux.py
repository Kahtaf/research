"""Serial Linux QA; preserve each test run and exact candidate pins."""
import datetime,hashlib,json,os,resource,subprocess
from pathlib import Path
ROOT=Path('/srv/android/asus-official-runtime-capture/preparation-v5');os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(240,240));resource.setrlimit(resource.RLIMIT_FSIZE,(64*1024**2,64*1024**2))
label=os.environ.get('V5_RUN_LABEL','qa-001');assert label.startswith('qa-') and label.replace('-','').isalnum()
pins=json.loads((ROOT/'tool-pins.json').read_bytes());before={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in pins};assert before==pins
# A label changes receipt filenames only; all fixture test code is pinned.
env=dict(os.environ,V5_QA_LABEL=label)
p=subprocess.run(['python3','-B',str(ROOT/'source/run_tests.py')],cwd=ROOT,capture_output=True,text=True,timeout=180,env=env)
storage=sum(p.stat().st_size for p in ROOT.rglob('*') if p.is_file());assert storage<=512*1024**2
log=p.stderr+'\n'+p.stdout
with (ROOT/'evidence'/str(label+'.log')).open('x') as f:f.write(log)
after={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in pins}
r={'owned_storage_bytes_after':storage,'owned_storage_limit_bytes':512*1024**2,'schema':1,'returncode':p.returncode,'tool_seal_sha256':hashlib.sha256((ROOT/'tool-pins.json').read_bytes()).hexdigest(),'tested_pins':before,'changed_during_tests':[n for n in pins if after[n]!=before[n]],'fixture_only':True,'actual_payload_reads':False,'original_lock_accessed':False}
with (ROOT/'evidence'/str(label+'-execution.json')).open('x') as f:json.dump(r,f,indent=2);f.write('\n')
print(json.dumps({'execution':r,'tests':json.loads((ROOT/'evidence'/str(label+'.json')).read_bytes()),'log_tail':log[-10000:]}));raise SystemExit(p.returncode)
