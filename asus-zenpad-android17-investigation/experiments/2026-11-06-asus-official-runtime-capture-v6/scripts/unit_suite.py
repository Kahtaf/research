"""Run inherited 115 or new environment cases without native engine execution."""
import json,os,resource,sys,time,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'source')]
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(120,120));resource.setrlimit(resource.RLIMIT_FSIZE,(48*1024**2,48*1024**2))
phase,label=sys.argv[1:];assert phase in ('baseline','effective')
modules=['test_capture','test_provenance','test_metadata_roles'] if phase=='baseline' else ['test_effective_bindings']
start=time.monotonic();suite=unittest.defaultTestLoader.loadTestsFromNames(modules);result=unittest.TextTestRunner(verbosity=2).run(suite)
u=resource.getrusage(resource.RUSAGE_SELF)
r={'tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'elapsed_seconds':round(time.monotonic()-start,3),'cpu_seconds':round(u.ru_utime+u.ru_stime,3),'max_rss_KiB':u.ru_maxrss,'fixture_only':True,'real_state_read':False}
with (ROOT/'evidence'/str(label+'-tests.json')).open('x') as f:json.dump(r,f,indent=2);f.write('\n')
print(json.dumps(r));raise SystemExit(0 if result.wasSuccessful() else 1)
