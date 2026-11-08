"""Exact production imports; identical tests; all output in this review spike."""
import sys
sys.dont_write_bytecode = True
import hashlib, importlib.util, json, unittest
from pathlib import Path
R = Path(__file__).resolve().parents[1]
P = R.parent / '2026-11-06-asus-stock-helper-dispatch-fix'
sys.path.insert(0, str(P / 'source/service'))
pins = json.loads((P / 'evidence/source-pins.json').read_text())
for name, expected in pins.items():
    assert hashlib.sha256((P/name).read_bytes()).hexdigest() == expected, name
import controller as C
name = sys.argv[1]
assert name in ('test_faults','test_regressions','test_nested_dispatch','test_shell_guards')
source = R / 'tests/service' / (name+'.py')
assert source.read_bytes() == (P/'tests/service'/source.name).read_bytes()
spec = importlib.util.spec_from_file_location(name, source)
m = importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m)
with (R/'evidence'/(name+'.txt')).open('w') as stream:
    result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(m))
receipt=dict(suite=name,tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),passed=result.wasSuccessful(),production_controller=C.__file__,test_copy_byte_identical=True,device_contacted=False)
if name=='test_shell_guards':receipt['shell_vectors']=len(m.CASES)
(R/'evidence'/(name+'.json')).write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt))
raise SystemExit(not result.wasSuccessful())
