from pathlib import Path
import importlib.util
import sys
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('fixed_remote', ROOT / '2026-11-06-asus-product-input-build-kit/scripts/remote.py')
remote = importlib.util.module_from_spec(spec)
spec.loader.exec_module(remote)
print(remote.run(Path(sys.argv[1]).read_text()), end='')
