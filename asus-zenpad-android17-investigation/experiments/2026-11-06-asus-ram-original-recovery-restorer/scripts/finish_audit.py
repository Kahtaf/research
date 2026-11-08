import sys,base64
from remote import R,REMOTE,call
source=(R/'source/policy_audit.c').read_bytes()
code='''from pathlib import Path
import os,resource,subprocess,json,base64,hashlib
r=Path(REMOTE);os.chdir(r);os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
os.environ['TMPDIR']=str(r/'artifacts')
p=r/'source/policy_audit.c';(r/'evidence/policy-audit-r1.c').write_bytes(p.read_bytes());p.write_bytes(base64.b64decode(SOURCE))
T=Path('/srv/android/asus-target-rescue/artifacts/tools-delivery');log=[]
def run(cmd):
 p=subprocess.run(list(map(str,cmd)),capture_output=True,text=True,timeout=40);log.append(dict(command=list(map(str,cmd)),returncode=p.returncode,stdout=p.stdout,stderr=p.stderr));(r/'evidence/audit-finish.json').write_text(json.dumps(log,indent=2)+'\\n');assert p.returncode==0,p.stderr;return p.stdout
run(['gcc','-O2','-I'+str(T/'libsepol/include'),'source/policy_audit.c',T/'libsepol/src/libsepol.a','-o','artifacts/policy_audit'])
(r/'evidence/policy-structure.json').write_text(run(['artifacts/policy_audit','artifacts/base-policy','artifacts/restore-sepolicy']))
run(['python3','-B','tests/policy_checks.py'])
run(['python3','-B','tests/concat_test.py'])
print('POLICY_AND_CONCAT_PASS')
'''.replace('REMOTE',repr(REMOTE)).replace('SOURCE',repr(base64.b64encode(source).decode()))
p=call(code,timeout=110);(R/'evidence/audit-finish.stdout').write_bytes(p.stdout);(R/'evidence/audit-finish.stderr').write_bytes(p.stderr);print(p.stdout.decode());sys.exit(p.returncode)
