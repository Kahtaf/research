from pathlib import Path
import os,resource,subprocess,json,hashlib,sys
R=Path(__file__).resolve().parents[1];assert str(R)=='/srv/android/asus-offline-stock-fallback-20261107'
os.chdir(R);sys.dont_write_bytecode=True
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(768*1024**2,768*1024**2));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
os.environ.update(TMPDIR=str(R/'artifacts'),LC_ALL='C',PYTHONDONTWRITEBYTECODE='1',SOURCE_DATE_EPOCH='1794009600')
T=Path('/srv/android/asus-target-rescue/artifacts/tools-delivery');logs=[]
if (R/'evidence/build-log.json').exists():logs=json.loads((R/'evidence/build-log.json').read_text())
def run(cmd):
 cmd=list(map(str,cmd));p=subprocess.run(cmd,capture_output=True,text=True,timeout=90)
 logs.append(dict(command=cmd,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr));(R/'evidence/build-log.json').write_text(json.dumps(logs,indent=2)+'\n')
 if p.returncode:raise RuntimeError(p.stderr+p.stdout)
 return p.stdout
assert hashlib.sha256((R/'inputs/integrated-policy').read_bytes()).hexdigest()=='4ec49d329396db332a9049cc4a25a886fe5c85a9aa6e2fc975ba1fcbc2060e21'
assert hashlib.sha256((R/'inputs/original-stock.manifest').read_bytes()).hexdigest()=='605cdec038dafe3dddabfe92b8bd6cd189734f740230dfc362d02a43421e4e47'
flags=['-O2','-Wall','-Wextra','-Werror','-Wno-unused-function','-Wno-misleading-indentation','-fno-ident','-Wl,--build-id=none']
for n in ([] if '--resume' in sys.argv else ['test_selector','test_source']):
 run(['gcc',*flags,'source/'+n+'.c','-o','artifacts/'+n]);print(run(['artifacts/'+n]),end='')
for src,name in [('rescue.c','os-rescue'),('supervisor.c','rescue-sd-supervisor'),('sd_frontend.c','rescue-sd'),('p10_restore.c','p10-restore')]:
 if '--resume' in sys.argv and src!='p10_restore.c':continue
 run(['aarch64-linux-gnu-gcc','-static',*flags,'source/'+src,'-o','artifacts/'+name])
for n in ['policy_build','policy_query','policy_constraints','policy_delta']:
 run(['gcc','-O2','-Wno-discarded-qualifiers','-I'+str(T/'libsepol/include'),'source/'+n+'.c',T/'libsepol/src/libsepol.a','-o','artifacts/'+n])
policy=R/'artifacts/sepolicy'
if policy.exists():policy.rename(R/'evidence'/('previous-policy-'+hashlib.sha256(policy.read_bytes()).hexdigest()))
(R/'evidence/policy-added-rules.txt').write_text(run(['artifacts/policy_build','inputs/integrated-policy','artifacts/sepolicy']))
(R/'evidence/actual-policy-delta.txt').write_text(run(['artifacts/policy_delta','inputs/integrated-policy','artifacts/sepolicy']))
run([T/'sefcontext_compile','source/file_contexts']);(R/'artifacts/file_contexts.bin').write_bytes((R/'source/file_contexts.bin').read_bytes())
run(['python3','-B','scripts/check_artifacts.py']);run(['python3','-B','scripts/assemble_common.py'])
print('OFFLINE_STOCK_CORE_BUILD_PASS')
