"""Only the established parent-authorized SSH transport."""
import importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('parent_remote',ROOT.parent/'2026-11-06-asus-product-input-build-kit/scripts/remote.py');parent=importlib.util.module_from_spec(s);s.loader.exec_module(parent)
run=parent.run
