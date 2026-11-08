#!/usr/bin/env python3
"""Deploy only owned source/fixtures to a fresh exclusive preparation prefix."""
import base64
import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
WRAPPER=ROOT.parent/'2026-11-06-asus-product-input-build-kit/scripts/remote.py'
spec=importlib.util.spec_from_file_location('parent_remote',WRAPPER)
remote=importlib.util.module_from_spec(spec);spec.loader.exec_module(remote)
files={}
for directory in ('source','tests','inputs'):
    for p in sorted((ROOT/directory).rglob('*')):
        if p.is_file() and '__pycache__' not in p.parts and 'tmp' not in p.relative_to(ROOT).parts:
            files[str(p.relative_to(ROOT))]=base64.b64encode(p.read_bytes()).decode()
for name in ('README.md','manifest.schema.json','tool-pins.json'):
    files[name]=base64.b64encode((ROOT/name).read_bytes()).decode()
script='''import base64,hashlib,json,os,resource
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
from pathlib import Path
root=Path('/srv/android/asus-official-runtime-capture')
if root.exists():
 if root.resolve()!=root or not root.is_dir():raise RuntimeError('Owned prefix must be canonical')
else:raise RuntimeError('Expected existing owned parent')
p=root/'preparation-v3';p.mkdir(mode=0o700)
(p/'evidence').mkdir(mode=0o700)
files=json.loads(%r)
for name,value in files.items():
 path=p/name;path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('xb') as f:f.write(base64.b64decode(value))
pins=json.loads((p/'tool-pins.json').read_bytes())
for name,digest in pins.items():
 if hashlib.sha256((p/name).read_bytes()).hexdigest()!=digest:raise RuntimeError(name)
print(json.dumps({'preparation':str(p),'files_uploaded':len(files),'tool_seal_sha256':hashlib.sha256((p/'tool-pins.json').read_bytes()).hexdigest(),'real_capture_executed':False}))
''' % json.dumps(files)
print(remote.run(script))
