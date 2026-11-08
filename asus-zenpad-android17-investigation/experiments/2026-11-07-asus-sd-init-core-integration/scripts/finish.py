from pathlib import Path
import subprocess,json,os,sys,resource
R=Path(__file__).resolve().parents[1];assert str(R)=='/srv/android/asus-sd-init-core-integration-20261107'
os.chdir(R);os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(768*1024**2,768*1024**2))
os.environ.update(TMPDIR=str(R/'artifacts'),LC_ALL='C',PYTHONDONTWRITEBYTECODE='1')
T=Path('/srv/android/asus-target-rescue/artifacts/tools-delivery');logs=json.loads((R/'evidence/build-log.json').read_text())
def run(cmd):
 cmd=list(map(str,cmd));p=subprocess.run(cmd,capture_output=True,text=True,timeout=90)
 logs.append(dict(command=cmd,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr));(R/'evidence/build-log.json').write_text(json.dumps(logs,indent=2)+'\n')
 if p.returncode:raise RuntimeError(p.stderr+p.stdout)
 return p.stdout
if '--relink-daemon' in sys.argv:
 run(['aarch64-linux-gnu-gcc','-static','-O2','-Wall','-Wextra','-Werror','-Wno-unused-function','-Wno-misleading-indentation','-fno-ident','-Wl,--build-id=none','source/rescue.c','-o','artifacts/os-rescue'])
if '--rebuild-policy' in sys.argv:
 run(['gcc','-O2','-Wno-discarded-qualifiers','-I'+str(T/'libsepol/include'),'source/policy_build.c',T/'libsepol/src/libsepol.a','-o','artifacts/policy_build'])
 policy=R/'artifacts/sepolicy'
 if policy.exists():policy.rename(R/'evidence'/('previous-policy-'+__import__('hashlib').sha256(policy.read_bytes()).hexdigest()))
 (R/'evidence/rules-and-stock-fs-labels.txt').write_text(run(['artifacts/policy_build','inputs/data-corrected-policy','artifacts/sepolicy']))
run(['gcc','-O2','-I'+str(T/'libsepol/include'),'source/policy_delta.c',T/'libsepol/src/libsepol.a','-o','artifacts/policy_delta'])
(R/'evidence/actual-policy-delta.txt').write_text(run(['artifacts/policy_delta','inputs/data-corrected-policy','artifacts/sepolicy']))
print(run(['python3','-B','scripts/check_artifacts.py']),end='')
print(run(['python3','-B','scripts/assemble_common.py']),end='')
