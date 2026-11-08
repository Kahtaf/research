from pathlib import Path
import importlib.util,json,sys
sys.dont_write_bytecode=True
S=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('authorized_remote',S.parent/'2026-11-06-asus-product-input-build-kit/scripts/remote.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
script=(S/sys.argv[1]).read_text()
result=m.run(script)
(S/'evidence'/sys.argv[2]).write_text(result)
try:
 data=json.loads(result);print(json.dumps({k:v for k,v in data.items()if k not in ['files','pins','logs','copies','payload']},indent=2)[:10000])
except ValueError:print(result[:6000])
