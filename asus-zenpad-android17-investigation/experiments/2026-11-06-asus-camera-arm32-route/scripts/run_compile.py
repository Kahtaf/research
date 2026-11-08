import sys
sys.dont_write_bytecode = True
from pathlib import Path
import importlib.util,json
r=Path(__file__).resolve().parents[1];base=r.parent
spec=importlib.util.spec_from_file_location('remote',base/'2026-11-06-asus-product-input-build-kit/scripts/remote.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
script='from pathlib import Path\np=Path("/srv/android/asus-camera-arm32-route/camera_abi_probe.c")\np.write_text('+repr((r/'fixture/camera_abi_probe.c').read_text())+')\n'+(r/'scripts/compile_abi.py').read_text()
out=m.run(script);(r/'evidence/abi-compile.txt').write_text(out);print(out[:5000])
