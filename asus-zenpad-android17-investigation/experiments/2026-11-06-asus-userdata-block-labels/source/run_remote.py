from pathlib import Path
import importlib.util,sys
sys.dont_write_bytecode=True
root=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('authorized_remote',root.parent/'2026-11-06-asus-product-input-build-kit/scripts/remote.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
result=m.run((root/'source'/sys.argv[1]).read_text())
(root/'evidence'/sys.argv[2]).write_text(result)
print(result[:26000])
