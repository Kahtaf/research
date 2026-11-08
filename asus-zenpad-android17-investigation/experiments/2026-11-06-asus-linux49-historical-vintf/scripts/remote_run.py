from pathlib import Path
import importlib.util, sys
sys.dont_write_bytecode = True
root = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('fixed_transport',root/'2026-11-06-asus-product-input-build-kit/scripts/remote.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
preamble = 'import os, resource, signal\nos.sched_setaffinity(0, {min(os.sched_getaffinity(0))})\nresource.setrlimit(resource.RLIMIT_AS, (1073741824,1073741824))\nresource.setrlimit(resource.RLIMIT_CPU, (70,70))\nsignal.alarm(90)\n'
try:
    result=m.run(preamble + Path(sys.argv[1]).read_text())
except Exception as e:
    Path(sys.argv[2]+'.error').write_text(str(e))
    raise
Path(sys.argv[2]).write_text(result)
print('Saved',sys.argv[2])
