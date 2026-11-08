import base64,importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('remote',ROOT.parent/'2026-11-06-asus-product-input-build-kit/scripts/remote.py');remote=importlib.util.module_from_spec(spec);spec.loader.exec_module(remote)
data=base64.b64encode((ROOT/'scripts/inspect_graph_names.py').read_bytes()).decode()
script='''import base64,subprocess,json,os,resource
from pathlib import Path
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
root=Path('/srv/android/asus-official-runtime-capture/preparation-v4')
with (root/'scripts/inspect_graph_names.py').open('xb') as f:f.write(base64.b64decode(DATA))
p=subprocess.run(['python3','-B',str(root/'scripts/inspect_graph_names.py')],capture_output=True,text=True,timeout=180)
print(json.dumps({'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr}))
'''.replace('DATA',repr(data))
r=json.loads(remote.run(script));(ROOT/'evidence/graph-name-inspection.json').write_text(r['stdout']);print(r['stdout']);print(r['stderr']);raise SystemExit(r['returncode'])
