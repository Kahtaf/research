from pathlib import Path
import subprocess as s,json,datetime,hashlib
R=Path('/srv/android/asus-android-runtime-network-parity-20261107');E=R/'evidence';status={'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'stages':[],'actual_os_boots':0}
assert json.loads((E/'build-result.json').read_text())['genuine_build_success']
try:
 for name,args in [('admit',[]),('corroborate_boot',[]),('prepare',[]),('execute',['patch']),('verify_cow',[]),('execute',['runtime']),('extract',[])]:
  if name=='execute' and args==['runtime']:status['actual_os_boots']+=1;assert status['actual_os_boots']==1
  cmd=['python3','-B',str(R/'scripts'/(name+'.py'))]+args
  p=s.run(cmd,stdin=s.DEVNULL);status['stages'].append(dict(name=name,args=args,exit=p.returncode));assert p.returncode==0,(name,p.returncode)
 status['pipeline_completed']=True
finally:
 status['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();(E/'startup-pipeline-result.json').write_text(json.dumps(status,indent=2))
