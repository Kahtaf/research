from pathlib import Path
import os,resource,subprocess,json
R=Path(__file__).resolve().parents[1];os.chdir(R)
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CORE,(0,0));os.environ.update(TMPDIR=str(R/'artifacts'),PYTHONDONTWRITEBYTECODE='1');logs=[]
commands=[['gcc','-O2','-Wall','-Wextra','-Wno-unused-function','-Wno-misleading-indentation','scripts/adversarial_core.c','-o','artifacts/review-adversarial-core'],['artifacts/review-adversarial-core'],['python3','-B','scripts/receipt_edges.py'],['gcc','-O2','-Wall','-Wextra','-Wno-unused-function','-Wno-misleading-indentation','scripts/handoff_server.c','-o','artifacts/review-handoff-server'],['python3','-B','scripts/handoff_tests.py']]
for cmd in commands:
 p=subprocess.run(cmd,capture_output=True,text=True,timeout=180);logs.append(dict(command=cmd,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr));(R/'evidence/review-extra.json').write_text(json.dumps(logs,indent=2)+'\n');print(cmd,p.returncode,flush=True);assert p.returncode==0,p.stderr
