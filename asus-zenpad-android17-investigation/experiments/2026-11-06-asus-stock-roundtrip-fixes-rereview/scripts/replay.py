"""Replay byte-identical copied tests with direct production imports."""
import importlib.util
import json
from pathlib import Path
import sys
import unittest

R = Path(__file__).resolve().parents[1]
P = R.parent / '2026-11-06-asus-stock-roundtrip-parent-fixes'
sys.dont_write_bytecode = True
sys.path.insert(0, str(P / 'source/service'))
import controller as C

name = sys.argv[1]
assert name in ('test_faults', 'test_regressions', 'test_shell_guards')
source = R / 'tests/service' / (name + '.py')
assert source.read_bytes() == (P / 'tests/service' / source.name).read_bytes()
spec = importlib.util.spec_from_file_location(name, source)
module = importlib.util.module_from_spec(spec)
sys.modules[name] = module
spec.loader.exec_module(module)
with (R / 'evidence' / (name + '.txt')).open('w') as stream:
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromModule(module))
receipt = dict(suite=name, tests=result.testsRun, failures=len(result.failures),
               errors=len(result.errors), passed=result.wasSuccessful(),
               production_controller=C.__file__, test_source=str(source),
               test_copy_byte_identical=True, device_contacted=False)
if name == 'test_shell_guards':
    receipt['shell_vectors'] = len(module.CASES)
(R / 'evidence' / (name + '.json')).write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps(receipt))
raise SystemExit(not result.wasSuccessful())
