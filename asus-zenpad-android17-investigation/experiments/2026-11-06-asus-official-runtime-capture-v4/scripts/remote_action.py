"""One checked synchronous action in the owned preparation; no build observation."""
import importlib.util
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('parent_remote',ROOT.parent/'2026-11-06-asus-product-input-build-kit/scripts/remote.py')
remote=importlib.util.module_from_spec(spec);spec.loader.exec_module(remote)
if sys.argv[1:] != ['graph']:
    raise SystemExit('only explicit graph qualification action')
script='''import json,os,resource,subprocess
from pathlib import Path
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
root=Path('/srv/android/asus-official-runtime-capture/preparation-v4')
p=subprocess.run(['python3','-B',str(root/'scripts/qualify_graph.py')],cwd=root,capture_output=True,text=True,timeout=1200)
print(json.dumps({'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr}))
'''
r=json.loads(remote.run(script))
with (ROOT/'evidence/actual-graph-qualification.json').open('x') as f:f.write(r['stdout'])
with (ROOT/'evidence/actual-graph-execution.json').open('x') as f:json.dump({'returncode':r['returncode'],'stderr':r['stderr']},f,indent=2);f.write('\n')
print(r['stdout']);print(r['stderr'])
raise SystemExit(r['returncode'])
