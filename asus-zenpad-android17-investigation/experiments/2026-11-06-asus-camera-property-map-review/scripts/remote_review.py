from pathlib import Path
import importlib.util,sys,subprocess,json,base64
sys.dont_write_bytecode=True
r=Path(__file__).resolve().parents[1]; workspace=r.parent
spec=importlib.util.spec_from_file_location('transport',workspace/'2026-11-06-asus-product-input-build-kit/scripts/remote.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
payload=Path(sys.argv[1]).read_text()
prefix='''import os,resource
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
resource.setrlimit(resource.RLIMIT_CPU,(40,40))
resource.setrlimit(resource.RLIMIT_FSIZE,(8*1024**2,8*1024**2))
'''
p=subprocess.run(m.SSH+['python3 -B -'],input=prefix+payload,text=True,capture_output=True,timeout=110)
(r/'evidence'/sys.argv[2]).write_text(p.stdout)
if p.stderr: print(p.stderr)
print(p.stdout[:6000]);assert p.returncode==0,p.returncode
