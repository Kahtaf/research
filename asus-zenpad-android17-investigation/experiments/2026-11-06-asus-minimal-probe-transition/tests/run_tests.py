#!/usr/bin/env python3
"""No subprocess/fork/network: audit installed before importing implementation/tests."""
import io
import json
import os
from pathlib import Path
import sys
import time
import unittest
ROOT = Path(__file__).resolve().parents[1]
BLOCKED = []

def forbid(event, args):
    if event in {'subprocess.Popen', 'os.system', 'os.posix_spawn', 'os.fork', 'os.forkpty',
                 'os.exec', 'pty.spawn'} or event.startswith('socket.'):
        BLOCKED.append(event)
        raise AssertionError('Offline audit blocked ' + event)

def main():
    os.umask(0o077)
    sys.addaudithook(forbid)
    sys.path[:0] = [str(ROOT / 'source'), str(ROOT / 'tests')]
    import test_adapter
    out = ROOT / 'evidence' / ('offline-' + str(time.time_ns()))
    out.mkdir(exist_ok=False)
    stream = io.StringIO()
    suite = unittest.defaultTestLoader.loadTestsFromModule(test_adapter)
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    (out / 'tests.txt').write_text(stream.getvalue())
    receipt = dict(tests=result.testsRun, failures=len(result.failures), errors=len(result.errors),
                   failure_details=[dict(test=str(t), traceback=s) for t,s in result.failures],
                   error_details=[dict(test=str(t), traceback=s) for t,s in result.errors],
                   audit_blocked_events=BLOCKED, actual_subprocess_calls=0, device_contacted=False,
                   code=test_adapter.a.code_receipt(), scenarios=test_adapter.SCENARIOS,
                   tests_sha256={p.name:test_adapter.a.sha(p.read_bytes()) for p in sorted((ROOT/'tests').glob('*.py'))},
                   limits='Offline fake command/storage behavior, no physical capture/boot/durability proof')
    (out / 'receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
    print(stream.getvalue())
    print(json.dumps(dict(evidence=str(out), tests=result.testsRun, failures=len(result.failures), errors=len(result.errors), audit_blocked_events=BLOCKED)))
    return 0 if result.wasSuccessful() and not BLOCKED else 1
if __name__ == '__main__':
    raise SystemExit(main())
