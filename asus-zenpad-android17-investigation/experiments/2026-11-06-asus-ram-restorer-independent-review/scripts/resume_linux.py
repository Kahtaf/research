from pathlib import Path
import os,resource,subprocess,json
R=Path(__file__).resolve().parents[1];os.chdir(R)
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
os.environ.update(TMPDIR=str(R/'artifacts'),PYTHONDONTWRITEBYTECODE='1',LC_ALL='C',RESCUE_TEST_SERVER=str(R/'artifacts/review-test_server'),RESCUE_DAEMON=str(R/'artifacts/review-os-rescue'))
(R/'artifacts/session_server').chmod(0o700)
T=Path('/srv/android/asus-target-rescue/artifacts/tools-delivery');log=[]
cmds=[['python3','-B','tests/'+x] for x in ['host_tests.py','host_durability.py','test_adapters.py','policy_checks.py']]
cmds += [['gcc','-O2','-I'+str(T/'libsepol/include'),'source/policy_audit.c',str(T/'libsepol/src/libsepol.a'),'-o','artifacts/review-policy_audit'],['artifacts/review-policy_audit','artifacts/base-policy','artifacts/restore-sepolicy']]
for cmd in cmds:
 p=subprocess.run(cmd,capture_output=True,text=True,timeout=180);log.append(dict(command=cmd,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr));(R/'evidence/review-resume.json').write_text(json.dumps(log,indent=2)+'\n');print(cmd,p.returncode,flush=True)
 assert p.returncode==0,p.stderr
(R/'evidence/review-resources.json').write_text(json.dumps(dict(cpu_affinity=sorted(os.sched_getaffinity(0)),address_space=resource.getrlimit(resource.RLIMIT_AS),serial=True))+'\n')
