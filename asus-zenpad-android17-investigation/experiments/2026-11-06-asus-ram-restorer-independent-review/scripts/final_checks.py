from pathlib import Path
import os,resource,subprocess,json,hashlib
R=Path(__file__).resolve().parents[1];os.chdir(R)
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CORE,(0,0));os.environ.update(TMPDIR=str(R/'artifacts'),PYTHONDONTWRITEBYTECODE='1');logs=[]
T=Path('/srv/android/asus-target-rescue/artifacts/tools-delivery')
commands=[['gcc','-O2','-Wall','-Wextra','-Wno-unused-function','-Wno-misleading-indentation','scripts/handoff_server-r2.c','-o','artifacts/review-handoff-server-r2'],['python3','-B','scripts/handoff_tests-r2.py'],['gcc','-O2','-Wno-discarded-qualifiers','-I'+str(T/'libsepol/include'),'source/policy_build.c',str(T/'libsepol/src/libsepol.a'),'-o','artifacts/review-policy-build'],['artifacts/review-policy-build','artifacts/base-policy','artifacts/review-sepolicy'],[str(T/'sefcontext_compile'),'-o','artifacts/review-file_contexts.bin','artifacts/file_contexts']]
for cmd in commands:
 p=subprocess.run(cmd,capture_output=True,text=True,timeout=90);logs.append(dict(command=cmd,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr));(R/'evidence/review-final.json').write_text(json.dumps(logs,indent=2)+'\n');print(cmd,p.returncode,flush=True);assert p.returncode==0,p.stderr
for a,b in [('review-sepolicy','restore-sepolicy'),('review-file_contexts.bin','file_contexts.bin')]:assert (R/'artifacts'/a).read_bytes()==(R/'artifacts'/b).read_bytes()
(R/'evidence/review-policy-reproduction.json').write_text(json.dumps(dict(passed=True,policy_sha256=hashlib.sha256((R/'artifacts/review-sepolicy').read_bytes()).hexdigest(),contexts_sha256=hashlib.sha256((R/'artifacts/review-file_contexts.bin').read_bytes()).hexdigest()))+'\n')
