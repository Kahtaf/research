from pathlib import Path
import subprocess as s,json,datetime,hashlib
R=Path('/srv/android/asus-vendor-bpf-load-compat-20261107');E=R/'evidence';t=(R/'run-candidate-r2/serial.log').read_text();assert 'CAPTURE_RETURN result=7' in t and 'REPLAY exact-captured fd=3 errno=0' in t
assert hashlib.sha256((R/'inputs/libbpf_android.candidate.so').read_bytes()).hexdigest()=='682ed7fd0c69bcf0567d81c4d0d43314fce1c0205172f6a1dd9c263a97c7389e'
status={'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'stages':[],'actual_os_boots':0,'candidate_runtime':True}
try:
 for name,args in [('admit',[]),('corroborate_boot',[]),('prepare',[]),('execute',['patch']),('verify_cow',[]),('execute',['runtime']),('extract',[])]:
  if name=='execute' and args==['runtime']:status['actual_os_boots']+=1;assert status['actual_os_boots']==1
  p=s.run(['python3','-B',str(R/'scripts'/(name+'.py'))]+args,stdin=s.DEVNULL);status['stages'].append(dict(name=name,args=args,exit=p.returncode));assert p.returncode==0,(name,p.returncode)
 status['pipeline_completed']=True
finally:
 status['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();(E/'startup-pipeline-result.json').write_text(json.dumps(status,indent=2))
