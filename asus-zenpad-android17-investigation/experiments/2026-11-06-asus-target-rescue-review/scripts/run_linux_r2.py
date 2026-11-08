"""Run only the corrected harness case in the existing owned review fixture."""
import json
import shlex
import subprocess
from run_linux_review import SSH, R, REMOTE

data=(R/'scripts/review_sessions_r2.py').read_bytes()
setup='import pathlib,sys; p=pathlib.Path('+repr(REMOTE+'/scripts/review_sessions_r2.py')+'); f=p.open("xb"); f.write(sys.stdin.buffer.read()); f.close()'
p=subprocess.run(SSH+['python3 -B -c '+shlex.quote(setup)],input=data,capture_output=True,timeout=30)
(R/'evidence/linux-r2-setup.stderr').write_bytes(p.stderr)
assert p.returncode==0
code='''import os,resource,subprocess,pathlib,json,sys
r=pathlib.Path('/srv/android/asus-target-rescue-review');os.chdir(r)
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
resource.setrlimit(resource.RLIMIT_CPU,(30,30))
os.environ['PYTHONDONTWRITEBYTECODE']='1';os.environ['RESCUE_TEST_SERVER']=str(r/'artifacts/test_server')
p=subprocess.run(['python3','-B','scripts/review_sessions_r2.py'],capture_output=True,text=True,timeout=10)
(r/'evidence/session-tests-r2.stdout').write_text(p.stdout);(r/'evidence/session-tests-r2.stderr').write_text(p.stderr)
print(json.dumps(dict(returncode=p.returncode,stdout=p.stdout,stderr=p.stderr,result=json.loads((r/'evidence/session-tests-r2.json').read_text()))))
sys.exit(p.returncode)
'''
p=subprocess.run(SSH+['python3 -B -c '+shlex.quote(code)],capture_output=True,timeout=25)
(R/'evidence/linux-r2-result.json').write_bytes(p.stdout)
(R/'evidence/linux-r2.stderr').write_bytes(p.stderr)
assert p.returncode==0
print(p.stdout.decode())
