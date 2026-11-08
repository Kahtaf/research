"""Serial bounded tests; refuses to create fixtures outside this isolated kit."""
from pathlib import Path
import os
import resource
import sys
import unittest
ROOT = Path(__file__).resolve().parents[1]
if sys.platform == 'linux':
    os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
    resource.setrlimit(resource.RLIMIT_AS, (1024 ** 3, 1024 ** 3))
    os.nice(10)
print('Fixture limits: serial; Linux affinity=1 CPU, RLIMIT_AS=1 GiB; no compiler or build engine', flush=True)
suite = unittest.defaultTestLoader.discover(str(ROOT / 'tests'), pattern='test_*.py')
result = unittest.TextTestRunner(verbosity=2).run(suite)
print('maxrss:', resource.getrusage(resource.RUSAGE_SELF).ru_maxrss, flush=True)
sys.exit(0 if result.wasSuccessful() else 1)
