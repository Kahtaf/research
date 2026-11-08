from pathlib import Path
import subprocess,os,json,resource
R=Path(__file__).resolve().parents[1];assert str(R)=='/srv/android/asus-offline-stock-fallback-20261107';os.chdir(R)
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(768*1024**2,768*1024**2));os.environ.update(TMPDIR=str(R/'artifacts'),LC_ALL='C',PYTHONDONTWRITEBYTECODE='1')
logs=json.loads((R/'evidence/build-log.json').read_text())
def run(cmd):
 p=subprocess.run(cmd,capture_output=True,text=True,timeout=90);logs.append(dict(command=cmd,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr));(R/'evidence/build-log.json').write_text(json.dumps(logs,indent=2)+'\n')
 if p.returncode:raise RuntimeError(p.stderr+p.stdout)
 print(p.stdout,end='')
flags=['-O2','-Wall','-Wextra','-Werror','-Wno-unused-function','-Wno-misleading-indentation','-fno-ident','-Wl,--build-id=none']
run(['gcc',*flags,'source/test_selector.c','-o','artifacts/test_selector']);run(['artifacts/test_selector'])
for src,out in [('rescue.c','os-rescue'),('supervisor.c','rescue-sd-supervisor'),('p10_restore.c','p10-restore')]:run(['aarch64-linux-gnu-gcc','-static',*flags,'source/'+src,'-o','artifacts/'+out])
run(['python3','-B','scripts/check_artifacts.py']);run(['python3','-B','scripts/assemble_common.py'])
