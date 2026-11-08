"""Small serial builds in this spike's owned VM prefix only."""
from pathlib import Path
import os,resource,subprocess,json,hashlib,sys
R=Path(__file__).resolve().parents[1]
assert str(R)=='/srv/android/asus-sd-init-core-integration-20261107'
os.chdir(R);sys.dont_write_bytecode=True
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
resource.setrlimit(resource.RLIMIT_AS,(768*1024**2,768*1024**2))
resource.setrlimit(resource.RLIMIT_CORE,(0,0))
os.environ.update(TMPDIR=str(R/'artifacts'),LC_ALL='C',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1',SOURCE_DATE_EPOCH='1794009600')
T=Path('/srv/android/asus-target-rescue/artifacts/tools-delivery')
logs=[]
logpath=R/'evidence/build-log.json'
if logpath.exists():logs=json.loads(logpath.read_text())
def run(cmd):
 cmd=list(map(str,cmd));p=subprocess.run(cmd,capture_output=True,text=True,timeout=90)
 logs.append(dict(command=cmd,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr));logpath.write_text(json.dumps(logs,indent=2)+'\n')
 if p.returncode:raise RuntimeError(p.stderr+p.stdout)
 return p.stdout
assert hashlib.sha256((R/'inputs/data-corrected-policy').read_bytes()).hexdigest()=='3d982859fdbf06336d6274e7e700ca64a2551effd769a8cb119b4fed97388815'
assert hashlib.sha256((R/'artifacts/rescue-sd').read_bytes()).hexdigest()=='0d7ad266bbe5fefc1ce7db8716d209ed3a6da3d4de124e1d99d84a4634d5e7cb'
flags=['-O2','-Wall','-Wextra','-Werror','-Wno-unused-function','-Wno-misleading-indentation','-fno-ident','-Wl,--build-id=none']
run(['gcc',*flags,'source/test_supervisor.c','-o','artifacts/test_supervisor'])
print(run(['artifacts/test_supervisor']),end='')
run(['aarch64-linux-gnu-gcc','-static',*flags,'source/rescue.c','-o','artifacts/os-rescue'])
run(['aarch64-linux-gnu-gcc','-static',*flags,'source/supervisor.c','-o','artifacts/rescue-sd-supervisor'])
for n in ['policy_build','policy_query','policy_constraints','policy_delta']:
 run(['gcc','-O2','-Wno-discarded-qualifiers','-I'+str(T/'libsepol/include'),'source/'+n+'.c',T/'libsepol/src/libsepol.a','-o','artifacts/'+n])
policy=R/'artifacts/sepolicy'
if policy.exists():policy.rename(R/'evidence'/('previous-policy-'+hashlib.sha256(policy.read_bytes()).hexdigest()))
log=run(['artifacts/policy_build','inputs/data-corrected-policy','artifacts/sepolicy'])
(R/'evidence/rules-and-stock-fs-labels.txt').write_text(log)
run([T/'sefcontext_compile','source/file_contexts'])
(R/'artifacts/file_contexts.bin').write_bytes((R/'source/file_contexts.bin').read_bytes())
(R/'evidence/actual-policy-delta.txt').write_text(run(['artifacts/policy_delta','inputs/data-corrected-policy','artifacts/sepolicy']))
run(['python3','-B','scripts/check_artifacts.py'])
run(['python3','-B','scripts/assemble_common.py'])
print('COMMON_CORE_BUILD_PASS')
