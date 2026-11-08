"""Review-owned fixture runner, established wrapper, no production reads."""
import base64, hashlib, importlib.util, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('approved_remote',ROOT.parent/'2026-11-06-asus-product-input-build-kit/scripts/remote.py')
remote=importlib.util.module_from_spec(spec);spec.loader.exec_module(remote)
phase=sys.argv[1]
assert phase in ('baseline','adversarial','adversarial-r2')
files={}
if phase=='baseline':
    for folder in ('source','tests','inputs'):
        for p in sorted((ROOT/folder).glob('*')):
            if p.is_file() and p.suffix in ('.py','.json'):
                files[str(p.relative_to(ROOT))]=base64.b64encode(p.read_bytes()).decode()
    for n in ('manifest.schema.json','host-metadata-source-plan.schema.json'):
        files[n]=base64.b64encode((ROOT/n).read_bytes()).decode()
else:
    files['review_adversarial.py' if phase=='adversarial' else 'review_adversarial_r2.py']=base64.b64encode((ROOT/'scripts/review_adversarial.py').read_bytes()).decode()
script=r'''
import base64,hashlib,json,os,resource,subprocess,time
from pathlib import Path
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
resource.setrlimit(resource.RLIMIT_CPU,(120,120))
resource.setrlimit(resource.RLIMIT_FSIZE,(48*1024**2,48*1024**2))
r=Path('/srv/android/asus-capture-v5-review-20261106')
if PHASE=='baseline':r.mkdir(mode=0o700)
assert r.resolve()==r and r.is_dir()
for n,b in FILES.items():
    p=r/n;p.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
    with p.open('xb') as f:f.write(base64.b64decode(b))
(r/'evidence').mkdir(exist_ok=True)
def size():
    total=sum(p.lstat().st_size for p in r.rglob('*') if p.is_file() and not p.is_symlink())
    assert total<=128*1024**2,total
    return total
before=size();start=time.monotonic()
env=dict(os.environ,V5_QA_LABEL='review-baseline',PYTHONDONTWRITEBYTECODE='1',TMPDIR=str(r/'tests/tmp'))
command=['python3','-B',str(r/('source/run_tests.py' if PHASE=='baseline' else ('review_adversarial.py' if PHASE=='adversarial' else 'review_adversarial_r2.py')))]
p=subprocess.run(command,cwd=r,capture_output=True,text=True,timeout=180,env=env)
log=p.stdout+'\n'+p.stderr
(r/'evidence'/str(PHASE+'.log')).write_text(log)
receipt={'phase':PHASE,'returncode':p.returncode,'elapsed_seconds':round(time.monotonic()-start,3),'cpu_affinity':sorted(os.sched_getaffinity(0)),'address_space_limit_bytes':resource.getrlimit(resource.RLIMIT_AS)[0],'cpu_limit_seconds':120,'wall_limit_seconds':180,'file_size_limit_bytes':48*1024**2,'storage_limit_bytes':128*1024**2,'owned_bytes_before':before,'owned_bytes_after':size(),'child_max_rss_KiB':resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,'child_cpu_seconds':resource.getrusage(resource.RUSAGE_CHILDREN).ru_utime+resource.getrusage(resource.RUSAGE_CHILDREN).ru_stime,'uploaded_sha256':{n:hashlib.sha256((r/n).read_bytes()).hexdigest() for n in FILES},'fixture_only':True,'production_state_read':False}
if PHASE=='baseline':receipt['suite']=json.loads((r/'evidence/review-baseline.json').read_bytes())
else:receipt['cases']=json.loads((r/('evidence/adversarial-cases.json' if PHASE=='adversarial' else 'evidence/adversarial-r2-cases.json')).read_bytes())
(r/'evidence'/str(PHASE+'-execution.json')).write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'receipt':receipt,'log':log}))
'''.replace('PHASE',repr(phase)).replace('FILES',repr(files))
result=json.loads(remote.run(script))
(ROOT/'evidence'/str(phase+'-execution.json')).write_text(json.dumps(result['receipt'],indent=2)+'\n')
(ROOT/'evidence'/str(phase+'.log')).write_text(result['log'])
print(json.dumps({k:v for k,v in result['receipt'].items() if k not in ('uploaded_sha256','cases')},indent=2))
if 'cases' in result['receipt']:print(json.dumps({k:v for k,v in result['receipt']['cases'].items() if k!='cases'},indent=2))
if result['receipt']['returncode']:raise SystemExit(result['receipt']['returncode'])
