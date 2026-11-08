#!/usr/bin/env python3
"""Fresh-process offline suite; audit hook blocks subprocesses and network access."""
import argparse
import contextlib
import io
import json
import os
from pathlib import Path
import platform
import sys
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
BLOCKED = []


def forbid_external(event, args):
    if event in {'subprocess.Popen', 'os.system', 'os.posix_spawn', 'os.fork', 'os.forkpty',
                 'os.exec', 'socket.connect', 'socket.bind', 'socket.getaddrinfo'}:
        BLOCKED.append(event)
        raise AssertionError('External operation forbidden in offline tests: ' + event)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    out = args.out or ROOT / 'evidence' / ('replay-' + str(time.time_ns()))
    if ROOT not in out.resolve().parents:
        raise ValueError('Output must stay inside this spike')
    out.mkdir(parents=True, exist_ok=False)
    os.umask(0o077)
    sys.addaudithook(forbid_external)
    sys.path.insert(0, str(ROOT / 'tests'))
    # Install the audit guard before importing any test or implementation module.
    import test_transport as transport
    import test_observer as observer
    import test_r3 as regression
    suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromModule(m)
                               for m in (transport, observer, regression))
    started = time.monotonic()
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    log = stream.getvalue()
    (out / 'tests.txt').write_text(log)
    receipts = transport.p.code_receipt()
    receipt = dict(tests_run=result.testsRun, failures=len(result.failures), errors=len(result.errors),
                   failure_details=[dict(test=str(test), traceback=trace) for test, trace in result.failures],
                   error_details=[dict(test=str(test), traceback=trace) for test, trace in result.errors],
                   elapsed_seconds=time.monotonic()-started, python=sys.version, platform=dict(zip(("sysname", "nodename", "release", "version", "machine"), os.uname())),
                   source_bundle=receipts, profile_sha256=transport.p.PROFILE_SHA,
                   test_source_pins={str(path.relative_to(ROOT)): transport.b.sha(path.read_bytes()) for path in sorted((ROOT / "tests").glob("*.py"))},
                   audit_blocked_events=BLOCKED, actual_subprocess_calls=0, device_contacted=False,
                   scope='Offline typed fake transport; physical boot and actual target captures unproved',
                   scenarios=transport.OBSERVATIONS, cli=transport.CLI_OBSERVATIONS)
    (out / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(log)
    print(json.dumps({k:receipt[k] for k in ('tests_run','failures','errors','elapsed_seconds','audit_blocked_events')}))
    return 0 if result.wasSuccessful() and not BLOCKED else 1


if __name__ == '__main__':
    raise SystemExit(main())
