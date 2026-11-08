"""Run host-only remote Python through the existing pinned SSH transport."""
from pathlib import Path
import importlib.util
import sys

workspace = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('transport', workspace / '2026-11-06-asus-product-input-build-kit/scripts/remote.py')
transport = importlib.util.module_from_spec(spec)
spec.loader.exec_module(transport)
print(transport.run(Path(sys.argv[1]).read_text()), end='', flush=True)
