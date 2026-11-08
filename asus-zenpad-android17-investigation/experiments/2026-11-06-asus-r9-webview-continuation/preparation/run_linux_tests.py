from pathlib import Path
import remote,base64
R=Path(__file__).resolve().parents[1]
f=base64.b64encode((R/'tests/test_r9.py').read_bytes()).decode()
s='TEST='+repr(f)+'\n'+r'''
from pathlib import Path
import base64,os,resource,subprocess,json,hashlib
R=Path('/srv/android/asus-reviewed-build-kit/r9');F=Path('/srv/android/asus-reviewed-build-kit/r9-fixtures')
(R/'tests').mkdir()
(R/'tests/test_r9.py').write_bytes(base64.b64decode(TEST))
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
p=subprocess.run(['python3','-B','-m','unittest','discover','-s',str(R/'tests'),'-v'],capture_output=True,text=True,cwd=F,timeout=240)
(R/'evidence/linux-tests.log').write_text(p.stdout+p.stderr)
result=dict(exit_code=p.returncode,one_cpu=True,address_space_bytes=1024**3,log_sha256=hashlib.sha256((p.stdout+p.stderr).encode()).hexdigest(),output=p.stdout+p.stderr)
(R/'evidence/linux-tests.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
'''
r=remote.run(s);(R/'evidence/linux-tests.json').write_text(r);print(r)
