from pathlib import Path
import importlib.util
s=importlib.util.spec_from_file_location('remote',str(Path(__file__).resolve().parents[2]/'2026-11-06-asus-product-input-build-kit/scripts/remote.py'))
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
run=m.run
if __name__=='__main__':
 import sys
 print(run(Path(sys.argv[1]).read_text()))
