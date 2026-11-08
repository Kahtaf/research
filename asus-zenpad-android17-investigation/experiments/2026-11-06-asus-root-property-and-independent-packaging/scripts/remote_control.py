"""Use the existing pinned SSH transport and store only compact task evidence."""
from pathlib import Path
import importlib.util
import sys

workspace = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('transport', workspace / '2026-11-06-asus-product-input-build-kit/scripts/remote.py')
transport = importlib.util.module_from_spec(spec)
spec.loader.exec_module(transport)
output = transport.run(Path(sys.argv[1]).read_text())
with Path(sys.argv[2]).open('x') as f:
    f.write(output)
print('Saved compact evidence to ' + sys.argv[2], flush=True)
