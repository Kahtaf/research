"""Owned fixture, existing compiler/libraries read-only, one CPU/1 GiB, no device."""
from pathlib import Path
import os,resource,subprocess,json,hashlib
R=Path(__file__).resolve().parents[1];os.chdir(R)
assert str(R)=='/srv/android/2026-11-06-asus-stock-only-ram-rescue-build'
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
os.environ.update(TMPDIR=str(R/'artifacts'),LC_ALL='C',SOURCE_DATE_EPOCH='1793923200',PYTHONDONTWRITEBYTECODE='1')
T=Path('/srv/android/asus-target-rescue/artifacts/tools-delivery');logs=[]
def run(cmd):
 p=subprocess.run([str(x) for x in cmd],capture_output=True,text=True,timeout=120)
 logs.append(dict(command=[str(x) for x in cmd],returncode=p.returncode,stdout=p.stdout,stderr=p.stderr))
 (R/'evidence/build-log.json').write_text(json.dumps(logs,indent=2)+'\n')
 if p.returncode:raise RuntimeError(p.stderr[-3000:])
 return p.stdout
pins=json.loads((R/'tool-pins.json').read_text())
for name,pin in pins.items():assert hashlib.sha256((T/name).read_bytes()).hexdigest()==pin
flags=['-static','-O2','-Wall','-Wextra','-Werror','-Wno-unused-function','-Wno-misleading-indentation','-Wl,--build-id=none']
run(['aarch64-linux-gnu-gcc',*flags,'-DP10_HANDOFF','source/rescue.c','-o','artifacts/os-rescue'])
run(['gcc','-O2','-Wno-discarded-qualifiers','-I'+str(T/'libsepol/include'),'source/policy_build.c',T/'libsepol/src/libsepol.a','-o','artifacts/policy_build'])
run(['artifacts/policy_build','artifacts/base-policy','artifacts/restore-sepolicy'])
run([T/'sefcontext_compile','artifacts/file_contexts'])
(R/'artifacts/rescue-proxy').write_bytes((T/'rescue-proxy').read_bytes())
run(['python3','-B','scripts/assemble_core.py'])
run(['aarch64-linux-gnu-gcc',*flags,'source/p10_restore.c','-o','artifacts/p10-restore'])
run(['aarch64-linux-gnu-gcc',*flags,'source/p10_restore.c','-o','artifacts/p10-restore-reproduction'])
assert (R/'artifacts/p10-restore').read_bytes()==(R/'artifacts/p10-restore-reproduction').read_bytes()
run(['aarch64-linux-gnu-readelf','-h','-l','artifacts/p10-restore'])
run(['python3','-B','scripts/assemble_final.py'])
for name in ['core_tests','session_server']:
 run(['gcc','-O2','-Wall','-Wextra','-Werror','-Wno-unused-function','-Wno-misleading-indentation','tests/'+name+'.c','-o','artifacts/'+name])
(R/'evidence/core-tests.json').write_text(run(['artifacts/core_tests']))
(R/'evidence/resources.json').write_text(json.dumps(dict(cpu_affinity=sorted(os.sched_getaffinity(0)),address_space=resource.getrlimit(resource.RLIMIT_AS),make_parallelism=1,device_operations=0))+'\n')
run(['aarch64-linux-gnu-gcc',*flags,'source/rescue.c','-o','artifacts/legacy-reproduction'])
assert hashlib.sha256((R/'artifacts/legacy-reproduction').read_bytes()).hexdigest()=='30ae9252e575d7c9c837783d60e51016a16bcadb46bd38215d8e49e5bb5d1c53'
run(['gcc','-O2','-Wall','-Wno-unused-function','-Wno-misleading-indentation','tests/test_server.c','-o','artifacts/test_server'])
os.environ['RESCUE_TEST_SERVER']=str(R/'artifacts/test_server');os.environ['RESCUE_DAEMON']=str(R/'artifacts/os-rescue')
run(['python3','-B','tests/test_adapters.py'])
run(['python3','-B','tests/host_tests.py'])
run(['python3','-B','tests/host_durability.py'])
run(['gcc','-O2','-I'+str(T/'libsepol/include'),'source/policy_audit.c',T/'libsepol/src/libsepol.a','-o','artifacts/policy_audit'])
(R/'evidence/policy-structure.json').write_text(run(['artifacts/policy_audit','artifacts/base-policy','artifacts/restore-sepolicy']))
run(['python3','-B','tests/policy_checks.py'])
run(['python3','-B','tests/contract_tests.py'])
run(['python3','-B','tests/new_manifest_tests.py'])
run(['gcc','-O2','-Wno-unused-function','tests/adversarial_core.c','-o','artifacts/adversarial_core'])
(R/'evidence/adversarial-core.json').write_text(run(['artifacts/adversarial_core']))
run(['gcc','-O2','-Wno-unused-function','tests/handoff_server-r2.c','-o','artifacts/review-handoff-server-r2'])
run(['python3','-B','tests/handoff_tests-r2.py'])
run(['python3','-B','tests/concat_test.py'])
run(['python3','-B','tests/reproduce.py'])
run(['python3','-B','scripts/verify_container.py'])
print('STOCK_ONLY_UNAPPROVED_OFFLINE_BUILD_PASS')
