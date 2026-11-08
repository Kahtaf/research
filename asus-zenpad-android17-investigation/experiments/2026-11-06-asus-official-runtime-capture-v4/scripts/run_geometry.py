import base64,importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('remote',ROOT.parent/'2026-11-06-asus-product-input-build-kit/scripts/remote.py');remote=importlib.util.module_from_spec(spec);spec.loader.exec_module(remote)
data=base64.b64encode((ROOT/'scripts/measure_blocks.py').read_bytes()).decode()
script='''import base64,subprocess,json
from pathlib import Path
root=Path('/srv/android/asus-official-runtime-capture/preparation-v4')
with (root/'scripts/measure_blocks.py').open('xb') as f:f.write(base64.b64decode(DATA))
p=subprocess.run(['python3','-B',str(root/'scripts/measure_blocks.py')],capture_output=True,text=True,timeout=180)
print(json.dumps({'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr}))
'''.replace('DATA',repr(data))
r=json.loads(remote.run(script));(ROOT/'evidence/frozen-graph-geometry.json').write_text(r['stdout']);print(r['stdout']);print(r['stderr']);raise SystemExit(r['returncode'])
