"""Serial offline re-review against immutable selected snapshot inputs."""
import ast
import gc
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

ROOT=Path(__file__).resolve().parents[1]
SPIKE=ROOT/'snapshot/workspace/2026-11-06-asus-usb-observation-dispatch-fix'
sys.dont_write_bytecode=True
resource.setrlimit(resource.RLIMIT_CPU,(60,60))
limit_errors={}
for name in ('RLIMIT_AS','RLIMIT_DATA','RLIMIT_RSS'):
    try:resource.setrlimit(getattr(resource,name),(1024**3,1024**3))
    except (ValueError,OSError) as error:limit_errors[name]=type(error).__name__
if hasattr(os,'sched_setaffinity'):os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
allowed={str(SPIKE/'tests/fake_shell.py'),str(SPIKE/'source/transport.py'),str(ROOT/'scripts/extra_child.py')}
real_popen=subprocess.Popen
children=[];audit_events=[];fixture_audit=[];outcomes=[]

def audit(event,args):
    if event=='subprocess.Popen':
        executable,argv,cwd,env=args
        if not (executable==sys.executable and len(argv)>=4 and
                argv[:3]==[sys.executable,'-B',str(ROOT/'scripts/guarded_child.py')] and argv[3] in allowed):
            raise RuntimeError('Blocked non-fixture child')
        audit_events.append(dict(event=event,argv=argv,env_keys=sorted(env) if env else None))
    if event in ('os.system','os.posix_spawn','os.exec','socket.connect','socket.bind','socket.getaddrinfo'):
        raise RuntimeError('Blocked external operation: '+event)
    if event=='socket.__new__':
        if args[1]!=socket.AF_UNIX:raise RuntimeError('Only AF_UNIX permitted')
        audit_events.append(dict(event=event,family=int(args[1])))
    if event=='open':
        path,mode,flags=args
        if isinstance(path,(str,bytes,os.PathLike)):
            target=Path(os.fsdecode(path)).absolute()
            if str(target).startswith('/dev/') or '/.ssh/' in str(target):
                raise RuntimeError('Device/private path blocked')
            if flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC) and not target.resolve().is_relative_to(ROOT):
                raise RuntimeError('Write outside review spike')

sys.addaudithook(audit)

def local_popen(argv,**kwargs):
    assert argv[:2]==[sys.executable,'-B'] and argv[2] in allowed
    assert not kwargs.get('shell')
    proc=real_popen([sys.executable,'-B',str(ROOT/'scripts/guarded_child.py'),*argv[2:]],**kwargs)
    children.append(proc)
    return proc

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module)
    return module

def digest(path):
    value=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024**2),b''):value.update(block)
    return value.hexdigest()

inputs=json.loads((ROOT/'evidence/inputs-before.json').read_text())
for record in inputs:assert digest(ROOT/record['snapshot'])==record['sha256']
old19=json.loads((ROOT/'evidence/old19-before.json').read_text())
for record in old19:
    assert digest(Path(record['original']))==digest(Path(record['old_snapshot']))==record['sha256']
original=Path(old19[3]['old_snapshot'])
def methods(path):
    tree=ast.parse(path.read_text())
    cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Cases')
    return {n.name:ast.dump(n,include_attributes=False) for n in cls.body
            if isinstance(n,ast.FunctionDef) and n.name.startswith('test_')}
baseline=methods(original);updated=methods(SPIKE/'tests/test_transport.py')
assert len(baseline)==32 and all(updated[name]==value for name,value in baseline.items())
module=load('fixed_fixture_tests',SPIKE/'tests/test_transport.py')
module.t.ADB=ROOT/'snapshot/host/adb'  # Mode 0400, hash input only, never executed.

class BoundedResult(unittest.TextTestResult):
    def stopTest(self,test):
        super().stopTest(test)
        rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        rss_bytes=rss if sys.platform=='darwin' else rss*1024
        assert rss_bytes<850_000_000
        d=getattr(test,'d',None)
        if d:
            for path in sorted(d.rglob('*.bin')):
                row=dict(test=test.id(),path=str(path.relative_to(ROOT)),bytes=path.stat().st_size,sha256=digest(path))
                if path.name=='request.bin':
                    data=path.read_bytes();assert data==module.Cases.measure.REQUEST
                    row.update(bytes=len(data),hex=data.hex())
                fixture_audit.append(row)
                if path.stat().st_size>1024**2:path.unlink()
        gc.collect()

started=time.monotonic()
summary={}
with patch.object(subprocess,'Popen',side_effect=local_popen):
    sets=[('supplied_38',module.Cases)]
    for name in ('prior_regressions','independent_checks'):
        extra=load(name,ROOT/f'scripts/{name}.py');extra.configure(module)
        sets.append((name,extra.IndependentCases))
    for name,cls in sets:
        result=unittest.TextTestRunner(verbosity=2,resultclass=BoundedResult).run(unittest.defaultTestLoader.loadTestsFromTestCase(cls))
        summary[name]=dict(tests=result.testsRun,failures=len(result.failures),errors=len(result.errors))
        outcomes.append(result.wasSuccessful())

assert all(p.poll() is not None for p in children)
summary.update(source_sha256=module.t.LOADED_SOURCE_SHA,baseline_32_methods_identical=True,
               children_launched=len(children),children_reaped=len(children),elapsed_seconds=time.monotonic()-started,
               actual_ADB_or_device_or_network=False,parallel_workers=0)
scale=1 if sys.platform=='darwin' else 1024
summary['peak_parent_rss_bytes']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*scale
summary['peak_child_rss_bytes']=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss*scale
summary['conservative_parent_plus_two_children_peak_bytes']=summary['peak_parent_rss_bytes']+2*summary['peak_child_rss_bytes']
assert summary['conservative_parent_plus_two_children_peak_bytes']<1024**3
summary['limits']={name:resource.getrlimit(getattr(resource,name)) for name in ('RLIMIT_CPU','RLIMIT_AS','RLIMIT_DATA','RLIMIT_RSS')}
summary['rejected_limit_settings']=limit_errors
summary['cpu_seconds_parent']=resource.getrusage(resource.RUSAGE_SELF).ru_utime+resource.getrusage(resource.RUSAGE_SELF).ru_stime
summary['cpu_seconds_children']=resource.getrusage(resource.RUSAGE_CHILDREN).ru_utime+resource.getrusage(resource.RUSAGE_CHILDREN).ru_stime
for record in inputs:assert digest(ROOT/record['snapshot'])==digest(Path(record['original']))==record['sha256']
for record in old19:assert digest(Path(record['original']))==digest(Path(record['old_snapshot']))==record['sha256']
summary['selected_inputs_unchanged']=len(inputs);summary['old_inputs_unchanged']=len(old19)
for name,value in (('test-summary',summary),('audit-events',audit_events),('fixture-audit',fixture_audit)):
    (ROOT/f'evidence/{name}.json').write_text(json.dumps(value,indent=2)+'\n')
print(json.dumps(summary,indent=2),flush=True)
raise SystemExit(not all(outcomes))
