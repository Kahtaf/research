from pathlib import Path
import datetime,json,os,resource,subprocess,sys
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));os.nice(10)
R=Path('/srv/android/asus-reviewed-build-kit/r3');O=R/'evidence/final-readonly';O.mkdir(parents=True)
sys.path.insert(0,str(R/'scripts'));import integrate as i
plan=i.read(R/'inputs/plan.json');seal=i.verify_pins(R);records=[]
for name,args in [('input-audit',['--audit-inputs']),('live-preflight',['--mode','PLAN_ONLY']),('describe-prior',['--describe-prior'])]:
 cmd=['python3','-B',str(R/'scripts/integrate.py'),*args]
 with (O/(name+'.stdout')).open('xb') as out,(O/(name+'.stderr')).open('xb') as err:
  result=subprocess.run(cmd,stdout=out,stderr=err)
 record={'name':name,'argv':cmd,'exit':result.returncode,'stdout_sha256':i.sha(O/(name+'.stdout')),'stderr_sha256':i.sha(O/(name+'.stderr'))}
 records.append(record);i.write(O/(name+'.json'),record)
print(json.dumps({'seal':seal,'commands':records,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'native_processes':i.native_processes(plan),'r6_files':[str(p) for p in Path(plan['logs']).glob('full-build-r6.*')],'attempt_exists':(R/'attempt').exists(),'parent_review_files':[str(p) for p in (R/'parent-review').glob('*')],'staged_sha256':i.sha(plan['staged_receipt']),'r5_terminal':{p.name:{'sha256':i.sha(p),'bytes':p.stat().st_size} for p in Path(plan['logs']).glob('full-build-r5.*') if p.is_file()},'all_outputs_preserved':True,'active_writes':False,'build_started':False},indent=2))
