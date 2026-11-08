"""Run only the copied fixture suite, blocking real ADB and network access."""
from pathlib import Path
import hashlib
import importlib.util
import json
import os
import resource
import socket
import subprocess
import sys
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
resource.setrlimit(resource.RLIMIT_CPU, (60, 60))
limit_errors = {}
try:
    resource.setrlimit(resource.RLIMIT_AS, (1024**3, 1024**3))
except (OSError, ValueError) as error:
    limit_errors['address_space'] = type(error).__name__
allowed = {str(ROOT/'tests/fake_shell.py'), str(ROOT/'source/transport.py')}
original_popen = subprocess.Popen
children = []
payloads = []

def audit(event, args):
    if event == 'subprocess.Popen':
        executable, argv, _, _ = args
        if not (executable == sys.executable and len(argv) >= 4 and
                argv[:3] == [sys.executable, '-B', str(ROOT/'scripts/guarded_child.py')]
                and argv[3] in allowed):
            raise RuntimeError('Blocked non-fixture child')
    if event in ('os.system', 'os.posix_spawn', 'os.exec', 'socket.connect',
                 'socket.bind', 'socket.getaddrinfo'):
        raise RuntimeError('Blocked external operation: ' + event)
    if event == 'socket.__new__' and args[1] != socket.AF_UNIX:
        raise RuntimeError('Only AF_UNIX permitted')
    if event == 'open':
        path, _, flags = args
        if isinstance(path, (str, bytes, os.PathLike)) and flags & (
                os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC):
            if not Path(path).absolute().is_relative_to(ROOT):
                raise RuntimeError('Write outside fix spike')

sys.addaudithook(audit)

def local_popen(argv, **kwargs):
    assert argv[:2] == [sys.executable, '-B'] and argv[2] in allowed
    assert not kwargs.get('shell')
    child = original_popen([sys.executable, '-B', str(ROOT/'scripts/guarded_child.py'),
                            *argv[2:]], **kwargs)
    children.append(child)
    return child

spec = importlib.util.spec_from_file_location('fixed_tests', ROOT/'tests/test_transport.py')
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

class BoundedResult(unittest.TextTestResult):
    def stopTest(self, test):
        super().stopTest(test)
        peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        assert peak < (1024**3 if sys.platform == 'darwin' else 1024**2)
        directory = getattr(test, 'd', None)
        if directory:
            for path in directory.rglob('*.bin'):
                data = path.read_bytes()
                payloads.append(dict(path=str(path.relative_to(ROOT)), bytes=len(data),
                                     sha256=hashlib.sha256(data).hexdigest()))
                if len(data) > 1024**2:
                    path.unlink()

started = time.monotonic()
with patch.object(subprocess, 'Popen', side_effect=local_popen):
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(module.Cases)
    result = unittest.TextTestRunner(verbosity=2, resultclass=BoundedResult).run(suite)
assert all(child.poll() is not None for child in children)
receipt = dict(tests=result.testsRun, failures=len(result.failures), errors=len(result.errors),
               elapsed_seconds=time.monotonic()-started, real_ADB_or_network=False,
               source_sha256=module.t.LOADED_SOURCE_SHA, children_reaped=len(children),
               peak_rss_platform_units=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
               limit_errors=limit_errors, payloads=payloads)
with (ROOT/'evidence/parent-tests.json').open('x') as stream:
    json.dump(receipt, stream, indent=2)
    stream.write('\n')
raise SystemExit(not result.wasSuccessful())
