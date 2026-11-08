import json,subprocess
from run_linux_review import R,REMOTE,SSH
files={n:(R/n).read_bytes().hex() for n in ['source/trace_server.c','scripts/trace_recovery.py']}
code='''
import os,resource,pathlib,subprocess,json,sys
R=pathlib.Path(payload['root']);os.chdir(R);os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(30,30))
for n,h in payload['files'].items():
 with (R/n).open('xb') as f:f.write(bytes.fromhex(h))
cmd=['gcc','-O2','-Wall','-Wextra','-Wno-unused-function','-Wno-misleading-indentation','source/trace_server.c','-o','artifacts/trace_server']
p=subprocess.run(cmd,capture_output=True,text=True,timeout=15)
(R/'evidence/trace-compile.json').write_text(json.dumps(dict(command=cmd,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr),indent=2))
assert p.returncode==0,p.stderr
os.environ['RESCUE_TEST_SERVER']=str(R/'artifacts/trace_server');os.environ['PYTHONDONTWRITEBYTECODE']='1'
p=subprocess.run(['python3','-B','scripts/trace_recovery.py'],capture_output=True,text=True,timeout=15)
print(json.dumps(dict(returncode=p.returncode,stdout=p.stdout,stderr=p.stderr,result=json.loads((R/'evidence/recovery-trace.json').read_text()))))
sys.exit(p.returncode)
'''
program='payload='+repr(dict(root=REMOTE,files=files))+'\n'+code
p=subprocess.run(SSH+['python3 -B -'],input=program,text=True,capture_output=True,timeout=45)
(R/'evidence/trace.stdout').write_text(p.stdout);(R/'evidence/trace.stderr').write_text(p.stderr)
assert p.returncode==0,p.stderr
(R/'evidence/recovery-trace.json').write_text(json.dumps(json.loads(p.stdout),indent=2)+'\n')
print(p.stdout)
