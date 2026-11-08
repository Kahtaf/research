from pathlib import Path
import importlib.util,json
R=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('remote',R/'remote_call.py')
spec=importlib.util.spec_from_file_location('fixed_remote',R.parents[1]/'2026-11-06-asus-product-input-build-kit/scripts/remote.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
script="from pathlib import Path\nO=Path('/srv/android/asus-final-netd-runtime-20261106')\n"
for name in ['fixture_init.c','run_unit.py']:
 script+='(O/"scripts"/'+repr(name)+').write_text('+repr((R/name).read_text())+')\n'
script+="exec(compile((O/'scripts/run_unit.py').read_text(),str(O/'scripts/run_unit.py'),'exec'))\n"
print(m.run(script),end='')
