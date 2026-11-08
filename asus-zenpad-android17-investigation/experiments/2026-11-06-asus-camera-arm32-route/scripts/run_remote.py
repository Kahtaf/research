#!/usr/bin/env python3
import sys
sys.dont_write_bytecode = True
import importlib.util, sys
from pathlib import Path
root = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('authorized_remote', root / '2026-11-06-asus-product-input-build-kit/scripts/remote.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
out = m.run(Path(sys.argv[1]).read_text())
Path(sys.argv[2]).write_text(out)
print(f'Saved {len(out)} bytes to {sys.argv[2]}')
print(out[:2000])
