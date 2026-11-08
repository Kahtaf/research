"""Run only isolated Linux fixture QA inside the fresh preparation prefix."""
import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('parent_remote',ROOT.parent/'2026-11-06-asus-product-input-build-kit/scripts/remote.py')
remote=importlib.util.module_from_spec(spec);spec.loader.exec_module(remote)
script=r'''import datetime,hashlib,json,os,platform,resource,subprocess
from pathlib import Path
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
root=Path('/srv/android/asus-official-runtime-capture/preparation-v3')
if root.resolve()!=root:raise RuntimeError('noncanonical preparation')
pins=json.loads((root/'tool-pins.json').read_bytes())
before={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in pins}
if before!=pins:raise RuntimeError('candidate drift before QA')
argv=['python3','-B',str(root/'source/run_tests.py')]
started=datetime.datetime.now(datetime.timezone.utc).isoformat()
p=subprocess.run(argv,cwd=root,text=True,capture_output=True,timeout=180)
log=p.stderr+'\n'+p.stdout
with (root/'evidence/linux-offline-tests.log').open('x') as f:f.write(log)
after={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in pins}
receipt={'schema':1,'started_utc':started,'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'argv':argv,'cwd':str(root),'returncode':p.returncode,'platform':platform.platform(),'python':platform.python_version(),'candidate_tool_seal_sha256':hashlib.sha256((root/'tool-pins.json').read_bytes()).hexdigest(),'tested_pins':before,'changed_during_tests':[name for name in pins if after[name]!=before[name]],'fixture_only':True,'actual_output_operations':False}
with (root/'evidence/linux-qa-execution.json').open('x') as f:json.dump(receipt,f,indent=2);f.write('\n')
print(json.dumps({'execution':receipt,'tests':json.loads((root/'evidence/linux-offline-tests.json').read_bytes()),'log':log}))
'''
result=json.loads(remote.run(script))
for key,name in (('execution','linux-qa-execution.json'),('tests','linux-offline-tests.json')):
    with (ROOT/'evidence'/name).open('x') as f:json.dump(result[key],f,indent=2);f.write('\n')
with (ROOT/'evidence/linux-offline-tests.log').open('x') as f:f.write(result['log'])
print(json.dumps({'returncode':result['execution']['returncode'],'tests':result['tests'],'changed_during_tests':result['execution']['changed_during_tests']}))
if result['execution']['returncode']:raise SystemExit(1)
