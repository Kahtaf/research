from pathlib import Path
import sys,json,base64,importlib.util
sys.dont_write_bytecode=True
r=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('authorized_remote',r.parent/'2026-11-06-asus-product-input-build-kit/scripts/remote.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
files={str(p.relative_to(r)):base64.b64encode(p.read_bytes()).decode() for folder in ['src','tests','backend','supplement','donor'] for p in (r/folder).rglob('*') if p.is_file()}
pre='''from pathlib import Path
import os,resource,base64
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
resource.setrlimit(resource.RLIMIT_CPU,(120,120))
resource.setrlimit(resource.RLIMIT_FSIZE,(64*1024**2,64*1024**2))
r=Path('/srv/android/asus-camera-property-map-20261106')
'''
pre+='files='+repr(files)+'\nfor rel,data in files.items():\n p=r/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(base64.b64decode(data))\n'
out=m.run(pre+(r/'scripts'/sys.argv[1]).read_text());(r/'evidence'/sys.argv[2]).write_text(out);print(out[:6000])
