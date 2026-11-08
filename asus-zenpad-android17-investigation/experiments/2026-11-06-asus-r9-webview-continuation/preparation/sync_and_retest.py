from pathlib import Path
import remote,base64,json
R=Path(__file__).resolve().parents[1]
files={str(p.relative_to(R)):base64.b64encode(p.read_bytes()).decode() for folder in ['scripts','tests'] for p in (R/folder).glob('*') if p.is_file()}
s='FILES='+repr(files)+'\n'+r'''
from pathlib import Path
import base64,subprocess,os,resource,json,hashlib
R=Path('/srv/android/asus-reviewed-build-kit/r9');F=Path('/srv/android/asus-reviewed-build-kit/r9-fixtures')
assert not (R/'inputs/kit-pins.json').exists()
for rel,b in FILES.items():(R/rel).write_bytes(base64.b64decode(b))
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
p=subprocess.run(['python3','-B','-m','unittest','discover','-s',str(R/'tests'),'-v'],capture_output=True,text=True,cwd=F,timeout=240)
result=dict(exit_code=p.returncode,one_cpu=True,address_space_bytes=1024**3,output=p.stdout+p.stderr)
with (R/'evidence/linux-tests-final.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(result,indent=2))
'''
r=remote.run(s);(R/'evidence/linux-tests-final.json').write_text(r);print(r)
