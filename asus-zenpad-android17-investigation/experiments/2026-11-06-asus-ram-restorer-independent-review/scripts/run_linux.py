from pathlib import Path
import os,resource,subprocess,json,hashlib
R=Path(__file__).resolve().parents[1];os.chdir(R)
assert str(R)=='/srv/android/2026-11-06-asus-ram-restorer-independent-review'
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
os.environ.update(TMPDIR=str(R/'artifacts'),PYTHONDONTWRITEBYTECODE='1',LC_ALL='C')
T=Path('/srv/android/asus-target-rescue/artifacts/tools-delivery');logs=[]
def run(cmd):
 p=subprocess.run(list(map(str,cmd)),capture_output=True,text=True,timeout=180)
 logs.append(dict(command=list(map(str,cmd)),returncode=p.returncode,stdout=p.stdout,stderr=p.stderr))
 (R/'evidence/review-run.json').write_text(json.dumps(logs,indent=2)+'\n')
 print(str(cmd)+': '+str(p.returncode),flush=True)
 if p.returncode:raise RuntimeError(p.stderr[-3000:])
 return p.stdout
for name,pin in json.loads((R/'tool-pins.json').read_text()).items():assert hashlib.sha256((T/name).read_bytes()).hexdigest()==pin
run(['python3','-B','scripts/verify_delivery.py'])
run(['python3','-B','scripts/verify_container.py'])
flags=['-static','-O2','-Wall','-Wextra','-Werror','-Wno-unused-function','-Wno-misleading-indentation','-Wl,--build-id=none']
for src,out,extra in [('rescue.c','review-os-rescue',['-DP10_HANDOFF']),('p10_restore.c','review-p10-restore',[]),('rescue.c','review-legacy',[])]:
 run(['aarch64-linux-gnu-gcc',*flags,*extra,'source/'+src,'-o','artifacts/'+out])
expected={'review-os-rescue':'os-rescue','review-p10-restore':'p10-restore','review-legacy':'legacy-reproduction'}
for a,b in expected.items():assert (R/'artifacts'/a).read_bytes()==(R/'artifacts'/b).read_bytes()
for name in ['core_tests','session_server','test_server']:
 run(['gcc','-O2','-Wall','-Wextra','-Wno-unused-function','-Wno-misleading-indentation','tests/'+name+'.c','-o','artifacts/review-'+name])
# Test runners select the local fixture server; originals are preserved in the local snapshot.
(R/'artifacts/session_server').write_bytes((R/'artifacts/review-session_server').read_bytes())
os.environ['RESCUE_TEST_SERVER']=str(R/'artifacts/review-test_server');os.environ['RESCUE_DAEMON']=str(R/'artifacts/review-os-rescue')
(R/'evidence/review-core.json').write_text(run(['artifacts/review-core_tests']))
for test in ['host_tests.py','host_durability.py','test_adapters.py','policy_checks.py']:
 run(['python3','-B','tests/'+test])
run(['gcc','-O2','-I'+str(T/'libsepol/include'),'source/policy_audit.c',T/'libsepol/src/libsepol.a','-o','artifacts/review-policy_audit'])
(R/'evidence/review-policy-structure.json').write_text(run(['artifacts/review-policy_audit','artifacts/base-policy','artifacts/restore-sepolicy']))
(R/'evidence/review-resources.json').write_text(json.dumps(dict(cpu_affinity=sorted(os.sched_getaffinity(0)),address_space=resource.getrlimit(resource.RLIMIT_AS),serial=True,source_and_tool_inputs_readonly=True))+'\n')
print('REVIEW_BASELINE_PASS',flush=True)
