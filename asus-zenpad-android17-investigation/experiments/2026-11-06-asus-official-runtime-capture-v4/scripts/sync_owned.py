"""Update only this unfinalized v4 candidate; preserve graph fixtures and evidence."""
import base64,hashlib,importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('remote',ROOT.parent/'2026-11-06-asus-product-input-build-kit/scripts/remote.py');remote=importlib.util.module_from_spec(spec);spec.loader.exec_module(remote)
files={}
for folder in ('source','inputs','tests','scripts'):
 for p in sorted((ROOT/folder).rglob('*')):
  if p.is_file() and '__pycache__' not in p.parts and 'tmp' not in p.relative_to(ROOT).parts:
   files[str(p.relative_to(ROOT))]=base64.b64encode(p.read_bytes()).decode()
for name in ('README.md','REPORT.md','tool-pins.json','manifest.schema.json'):files[name]=base64.b64encode((ROOT/name).read_bytes()).decode()
script='''import base64,hashlib,json,os,resource
from pathlib import Path
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
resource.setrlimit(resource.RLIMIT_CPU,(30,30))
root=Path('/srv/android/asus-official-runtime-capture/preparation-v4')
if root.resolve()!=root or (root/'FINALIZED.json').exists():raise RuntimeError('unfinalized owned v4 only')
files=json.loads(DATA)
for name,data in files.items():
 path=root/name
 if path.is_symlink():raise RuntimeError('symlink')
 path.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
 with path.open('wb') as f:f.write(base64.b64decode(data))
pins=json.loads((root/'tool-pins.json').read_bytes())
for name,digest in pins.items():
 if hashlib.sha256((root/name).read_bytes()).hexdigest()!=digest:raise RuntimeError('pin drift')
print(json.dumps({'preparation':str(root),'files':len(files),'candidate_seal':hashlib.sha256((root/'tool-pins.json').read_bytes()).hexdigest()}))
'''.replace('DATA',repr(json.dumps(files)))
print(remote.run(script))
