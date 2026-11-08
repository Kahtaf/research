"""Resume after owned Unix socket path-length failure; no original writes."""
from pathlib import Path
import os,resource,subprocess,json,hashlib
R=Path(__file__).resolve().parents[1];O=Path('/srv/android/2026-11-06-asus-stock-only-ram-rescue-build')
assert str(R)=='/srv/android/2026-11-06-stock-review'
os.chdir(R);os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
os.environ.update(PYTHONDONTWRITEBYTECODE='1',TMPDIR=str(R/'artifacts'),LC_ALL='C',SOURCE_DATE_EPOCH='1793923200',RESCUE_TEST_SERVER=str(R/'artifacts/test_server'),RESCUE_DAEMON=str(R/'artifacts/os-rescue'))
logs=[]
def run(cmd,timeout=120):
    p=subprocess.run(list(map(str,cmd)),capture_output=True,text=True,timeout=timeout)
    logs.append(dict(command=list(map(str,cmd)),returncode=p.returncode,stdout=p.stdout,stderr=p.stderr))
    (R/'evidence/review-resume.json').write_text(json.dumps(logs,indent=2)+'\n')
    assert p.returncode==0,(cmd,p.stderr[-2500:],p.stdout[-1500:]);return p.stdout
T=Path('/srv/android/asus-target-rescue/artifacts/tools-delivery')
for name in ['test_adapters.py','host_tests.py','host_durability.py','contract_tests.py','new_manifest_tests.py','handoff_tests-r2.py']:
    run(['python3','-B','tests/'+name])
run(['gcc','-O2','-I'+str(T/'libsepol/include'),'source/policy_audit.c',T/'libsepol/src/libsepol.a','-o','artifacts/policy_audit'])
(R/'evidence/review-policy-structure.json').write_text(run(['artifacts/policy_audit','artifacts/base-policy','artifacts/restore-sepolicy']))
run(['python3','-B','tests/policy_checks.py'])
run(['python3','-B','tests/reproduce.py'])
run(['python3','-B','scripts/verify_container.py'])
run(['python3','-B','scripts/host_edges.py'])
run(['python3','-B','scripts/readonly_reconciliation.py'])
before=json.loads((R/'evidence/remote-inputs-before.json').read_text())
after={str(f.relative_to(O)):dict(bytes=f.stat().st_size,sha256=hashlib.sha256(f.read_bytes()).hexdigest()) for f in sorted(O.rglob('*')) if f.is_file()}
assert before==after
(R/'evidence/remote-input-integrity.json').write_text(json.dumps(dict(passed=True,file_count=len(before),all_inputs_unchanged=True,pins=after),indent=2)+'\n')
(R/'evidence/resources.json').write_text(json.dumps(dict(cpu_affinity=sorted(os.sched_getaffinity(0)),address_space=resource.getrlimit(resource.RLIMIT_AS),sequential=True,device_operations=0))+'\n')
print('INDEPENDENT_LINUX_REVIEW_PASS')
