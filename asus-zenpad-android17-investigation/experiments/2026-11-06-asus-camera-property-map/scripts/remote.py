import sys
sys.dont_write_bytecode = True
from pathlib import Path
import importlib.util
base = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('authorized_remote', base/'2026-11-06-asus-product-input-build-kit/scripts/remote.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
script = Path(sys.argv[1]).read_text()
prefix = '''import os,resource
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
resource.setrlimit(resource.RLIMIT_CPU,(120,120))
resource.setrlimit(resource.RLIMIT_FSIZE,(64*1024**2,64*1024**2))
'''
out = m.run(prefix+script)
Path(sys.argv[2]).write_text(out)
print(out[:12000])
