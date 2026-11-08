from pathlib import Path
import importlib.util,sys
spec=importlib.util.spec_from_file_location('fixed_remote',Path(__file__).resolve().parents[2]/'2026-11-06-asus-product-input-build-kit/scripts/remote.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
print(m.run(Path(sys.argv[1]).read_text()),end='')
