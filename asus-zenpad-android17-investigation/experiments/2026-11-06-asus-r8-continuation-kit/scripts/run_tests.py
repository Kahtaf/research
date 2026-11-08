"""One-process test suite, one CPU and 1 GiB virtual memory ceiling on Linux."""
from pathlib import Path
import os,resource,sys,unittest
R=Path(__file__).resolve().parents[1]
if hasattr(os,'sched_getaffinity'):os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
if sys.platform=='linux':resource.setrlimit(resource.RLIMIT_AS,(1073741824,1073741824))
os.environ.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.discover(str(R/'tests'),pattern='test_*.py'))
raise SystemExit(not result.wasSuccessful())
