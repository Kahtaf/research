#!/usr/bin/env python3
"""Offline synthetic QA on Linux, serial, one CPU and 1 GiB address space."""
import json
import os
from pathlib import Path
import resource
import sys
import time
import unittest

ROOT=Path(__file__).resolve().parents[1]
if sys.platform!='linux':
    raise SystemExit('Use Linux for the explicit one-CPU/1-GiB QA contract')
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
resource.setrlimit(resource.RLIMIT_CPU,(120,120))
start=time.monotonic()
suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern='test_*.py')
result=unittest.TextTestRunner(verbosity=2).run(suite)
receipt={'schema':1,'fixture_only':True,'actual_AOSP_outputs_read':False,'actual_build_lock_acquired':False,
    'cpu_affinity':sorted(os.sched_getaffinity(0)),'cpu_count':len(os.sched_getaffinity(0)),
    'address_space_limit_bytes':resource.getrlimit(resource.RLIMIT_AS)[0],'cpu_seconds_limit':120,
    'tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
    'elapsed_seconds':round(time.monotonic()-start,3),'max_rss_KiB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
with (ROOT/'evidence/linux-offline-tests.json').open('x') as f:
    json.dump(receipt,f,indent=2);f.write('\n')
print(json.dumps(receipt))
raise SystemExit(0 if result.wasSuccessful() else 1)
