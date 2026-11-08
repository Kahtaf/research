"""Run the two actual production-path partial-publication regressions."""
from pathlib import Path
import json
import resource
import signal
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'review'))
import focused

resource.setrlimit(resource.RLIMIT_CPU, (30, 30))
signal.alarm(50)
sys.addaudithook(focused.a.audit)
names = (
    'review_direct_partial_success_then_write_error_records_unknown',
    'review_cli_partial_unknown_then_recovered_sink_records_unknown',
)
result = unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(
    focused.Focused(name) for name in names))
report = dict(tests=result.testsRun, failures=len(result.failures), errors=len(result.errors),
              children_created=len(focused.base.CHILDREN),
              all_children_reaped=all(p.returncode is not None for p in focused.base.CHILDREN),
              unreaped_registry_count=len(focused.UNREAPED_CHILDREN),
              observations=focused.a.OBSERVATIONS)
print(json.dumps(report))
sys.exit(not result.wasSuccessful())
