from pathlib import Path
import importlib.util,json
R=Path(__file__).resolve().parents[1];s=importlib.util.spec_from_file_location('remote',R/'scripts/remote.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
code='''
from pathlib import Path
import hashlib,json,os,resource,subprocess,time
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1073741824,1073741824))
K=Path('/srv/android/asus-reviewed-build-kit/r7')
rows=[]
for args in [['python3','-B',str(K/'scripts/run_tests.py')],['python3','-B',str(K/'scripts/integrate.py'),'--audit-inputs']]:
 start=time.monotonic();p=subprocess.run(args,text=True,capture_output=True)
 rows.append(dict(argv=args,exit=p.returncode,stdout=p.stdout,stderr=p.stderr,elapsed_seconds=time.monotonic()-start))
 if p.returncode:break
print(json.dumps(dict(results=rows,seal=hashlib.sha256((K/'inputs/kit-pins.json').read_bytes()).hexdigest(),attempt_exists=(K/'attempt').exists(),r7_markers=[str(p) for p in Path('/srv/android/asus-device-product/logs').glob('full-build-r7.*')],native_build_started=False,actual_product_dumpvars_run=False)))
'''
r=json.loads(m.run(code));(R/'evidence/linux-tests-and-source-audit.json').write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
for row in r['results']:print(json.dumps(row,indent=2))
print(json.dumps({k:v for k,v in r.items() if k!='results'},indent=2))
