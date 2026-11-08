"""Sequential offline tests against untouched, hash-bound snapshot bytes."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import resource
import socket
import subprocess
import sys
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--only-freshness', action='store_true')
options = parser.parse_args()
suffix = '-freshness' if options.only_freshness else ''
SPIKE = ROOT / 'snapshot/workspace/2026-11-06-asus-readonly-rescue-usb-transport'
sys.dont_write_bytecode = True
resource.setrlimit(resource.RLIMIT_CPU, (60, 60))
limit_errors = {}
for name in ('RLIMIT_AS', 'RLIMIT_DATA', 'RLIMIT_RSS'):
    try:
        resource.setrlimit(getattr(resource, name), (1024**3, 1024**3))
    except (ValueError, OSError) as error:
        limit_errors[name] = type(error).__name__
audit_events = []
allowed = {str(SPIKE / 'tests/fake_shell.py'), str(SPIKE / 'source/transport.py'), str(ROOT / 'scripts/extra_child.py')}
real_popen = subprocess.Popen

def audit(event, args):
    if event == 'subprocess.Popen':
        executable, argv, cwd, env = args
        if not (executable == sys.executable and argv[:3] == [sys.executable, '-B', str(ROOT / 'scripts/guarded_child.py')]
                and len(argv) >= 4 and argv[3] in allowed):
            raise RuntimeError('Blocked non-fixture child')
        audit_events.append(dict(event=event, argv=argv, env=env))
    if event in ('os.system', 'os.posix_spawn', 'os.exec', 'socket.connect', 'socket.bind', 'socket.getaddrinfo'):
        raise RuntimeError('Blocked external operation: ' + event)
    if event == 'socket.__new__':
        if args[1] != socket.AF_UNIX:
            raise RuntimeError('Only AF_UNIX permitted')
        audit_events.append(dict(event=event, family=int(args[1])))
    if event == 'open':
        path, mode, flags = args
        if isinstance(path, (str, bytes, os.PathLike)) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC):
            if not Path(path).absolute().is_relative_to(ROOT):
                raise RuntimeError('Write outside review spike')

sys.addaudithook(audit)

def local_popen(argv, **kwargs):
    assert argv[:2] == [sys.executable, '-B'] and argv[2] in allowed, argv
    assert not kwargs.get('shell')
    return real_popen([sys.executable, '-B', str(ROOT / 'scripts/guarded_child.py'), *argv[2:]], **kwargs)

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

records = json.loads((ROOT / 'evidence/inputs-before.json').read_text())
for record in records:
    assert hashlib.sha256((ROOT / record['snapshot']).read_bytes()).hexdigest() == record['sha256']

test_module = load('original_fixture_tests', SPIKE / 'tests/test_transport.py')
t = test_module.t
t.ADB = ROOT / 'snapshot/host/adb'  # Hash input only; never executable.
summary = {}
fixture_audit = []

class BoundedResult(unittest.TextTestResult):
    def stopTest(self, test):
        super().stopTest(test)
        assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss < 850_000_000
        directory = getattr(test, 'd', None)
        if directory is None:
            return
        for path in sorted(directory.rglob('*.bin')):
            data = path.read_bytes()
            row = dict(test=test.id(), path=str(path.relative_to(ROOT)), bytes=len(data),
                       sha256=hashlib.sha256(data).hexdigest())
            if path.name == 'request.bin':
                row['hex'] = data.hex()
            fixture_audit.append(row)
            if len(data) > 1024**2:
                path.unlink()

with patch.object(subprocess, 'Popen', side_effect=local_popen):
    if not options.only_freshness:
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(test_module.Cases)
        result = unittest.TextTestRunner(verbosity=2, resultclass=BoundedResult).run(suite)
        summary['original_suite'] = dict(tests=result.testsRun, failures=len(result.failures), errors=len(result.errors))
        if not result.wasSuccessful():
            raise SystemExit('Original suite failed')
    extra = load('independent_checks', ROOT / 'scripts/independent_checks.py')
    extra.configure(test_module)
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(extra.IndependentCases)
    if options.only_freshness:
        suite = unittest.TestSuite([extra.IndependentCases('test_reproduce_expired_binding_at_request_dispatch')])
    result = unittest.TextTestRunner(verbosity=2, resultclass=BoundedResult).run(
        suite)
    summary['independent_suite'] = dict(tests=result.testsRun, failures=len(result.failures), errors=len(result.errors))

summary['peak_parent_rss_bytes'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
summary['peak_child_rss_bytes'] = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
summary['conservative_parent_plus_two_children_peak_bytes'] = summary['peak_parent_rss_bytes'] + 2*summary['peak_child_rss_bytes']
assert summary['conservative_parent_plus_two_children_peak_bytes'] < 1024**3
summary['limits'] = dict(address_space=resource.getrlimit(resource.RLIMIT_AS),
                         data=resource.getrlimit(resource.RLIMIT_DATA), rss=resource.getrlimit(resource.RLIMIT_RSS),
                         rejected_limit_settings=limit_errors,
                         cpu_seconds=60, parallel_workers=0,
                         external_operations='blocked', child_targets='guarded fake shell and PLAN_ONLY only')
(ROOT / f'evidence/audit-events{suffix}.json').write_text(json.dumps(audit_events, indent=2) + '\n')
(ROOT / f'evidence/fixture-audit{suffix}.json').write_text(json.dumps(fixture_audit, indent=2) + '\n')
(ROOT / f'evidence/test-summary{suffix}.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps(summary, indent=2), flush=True)
raise SystemExit(not result.wasSuccessful())
