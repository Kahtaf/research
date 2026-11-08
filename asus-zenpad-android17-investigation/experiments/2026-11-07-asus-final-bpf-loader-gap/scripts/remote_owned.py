from pathlib import Path
import importlib.util
import sys
s = importlib.util.spec_from_file_location('remote', str(Path(__file__).resolve().parents[2] / '2026-11-06-asus-product-input-build-kit/scripts/remote.py'))
m = importlib.util.module_from_spec(s)
s.loader.exec_module(m)
if __name__ == '__main__':
    print(m.run(Path(sys.argv[1]).read_text()))
