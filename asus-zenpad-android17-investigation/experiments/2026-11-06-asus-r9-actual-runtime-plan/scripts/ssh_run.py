from pathlib import Path
import importlib.util, sys
sys.dont_write_bytecode=True
S=Path(__file__).resolve().parents[1]
p=S.parent/'2026-11-06-asus-product-input-build-kit/scripts/remote.py'
spec=importlib.util.spec_from_file_location('authorized_remote',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
result=m.run((S/sys.argv[1]).read_text())
(S/'evidence'/sys.argv[2]).write_text(result)
print(result[:16000])
