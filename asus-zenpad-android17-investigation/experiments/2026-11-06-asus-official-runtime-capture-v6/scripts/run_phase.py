"""Serial tiny-fixture phases, bounded and exclusive receipts; no real graph access."""
import argparse,datetime,hashlib,json,os,resource,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(240,240));resource.setrlimit(resource.RLIMIT_FSIZE,(48*1024**2,48*1024**2))
p=argparse.ArgumentParser();p.add_argument('phase',choices=('baseline','effective','review23','duplicate-before','duplicate-after'));p.add_argument('label');a=p.parse_args()
assert a.label.replace('-','').isalnum()
assert ROOT==Path('/srv/android/asus-official-runtime-capture/preparation-v6') and not (ROOT/'FINALIZED.json').exists()
(ROOT/'tests/tmp').mkdir(exist_ok=True)
def bytes_used():
 total=sum(p.lstat().st_size for p in ROOT.rglob('*') if p.is_file() and not p.is_symlink());assert total<=128*1024**2;return total
def hash_file(p):return hashlib.sha256(p.read_bytes()).hexdigest()
pins=json.loads((ROOT/'tool-pins.json').read_bytes());before={n:hash_file(ROOT/n) for n in pins};assert before==pins
size_before=bytes_used();start=time.monotonic();env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',TMPDIR=str(ROOT/'tests/tmp'),V6_CASE_LABEL=a.label+'-cases')
if a.phase in ('baseline','effective'):
 command=[sys.executable,'-B',str(ROOT/'scripts/unit_suite.py'),a.phase,a.label]
elif a.phase=='review23':command=[sys.executable,'-B',str(ROOT/'scripts/review_23.py')]
else:command=[sys.executable,'-B',str(ROOT/'scripts/parent_duplicate_4.py'),str(ROOT/('inputs/parent-duplicate/graph-before.py' if a.phase=='duplicate-before' else 'source/graph.py'))]
def child_bounds():
 resource.setrlimit(resource.RLIMIT_CPU,(120,120))
result=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,text=True,timeout=180,preexec_fn=child_bounds)
log=result.stdout+'\n'+result.stderr
with (ROOT/'evidence'/str(a.label+'.log')).open('x') as f:f.write(log)
after={n:hash_file(ROOT/n) for n in pins};changed=[n for n in pins if before[n]!=after[n]]
if a.phase in ('baseline','effective'):cases=json.loads((ROOT/'evidence'/str(a.label+'-tests.json')).read_bytes());success=result.returncode==0 and cases['failures']==cases['errors']==0
elif a.phase=='review23':cases=json.loads((ROOT/'evidence'/str(a.label+'-cases.json')).read_bytes());success=result.returncode==0 and cases['tests_run']==cases['expectations_met']==23
else:
 cases=json.loads(result.stdout);success=(result.returncode==1 and not cases['all_pass'] and [c['pass'] for c in cases['cases']]==[True,False,False,True]) if a.phase=='duplicate-before' else result.returncode==0 and cases['all_pass']
usage=resource.getrusage(resource.RUSAGE_CHILDREN)
r={'schema':1,'phase':a.phase,'label':a.label,'success':success and not changed,'returncode':result.returncode,'elapsed_seconds':round(time.monotonic()-start,3),'child_cpu_seconds':round(usage.ru_utime+usage.ru_stime,3),'max_child_rss_KiB':usage.ru_maxrss,'cpu_count':len(os.sched_getaffinity(0)),'address_space_limit_bytes':1024**3,'child_cpu_limit_seconds':120,'wall_timeout_seconds':180,'per_file_limit_bytes':48*1024**2,'new_allocation_limit_bytes':128*1024**2,'owned_bytes_before':size_before,'owned_bytes_after':bytes_used(),'tool_seal_sha256':hash_file(ROOT/'tool-pins.json'),'tested_pins':before,'changed_during_phase':changed,'cases':cases,'fixture_only':True,'real_state_read':False,'native_engine_executed':False,'process_signals_sent':False,'timeout_fired':False}
with (ROOT/'evidence'/str(a.label+'-execution.json')).open('x') as f:json.dump(r,f,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in r.items() if k not in ('tested_pins','cases')}));print(json.dumps({k:v for k,v in cases.items() if k!='cases'}));raise SystemExit(0 if r['success'] else 1)
