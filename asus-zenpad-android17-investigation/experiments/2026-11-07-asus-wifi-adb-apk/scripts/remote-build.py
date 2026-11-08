#!/usr/bin/env python3
"""Upload only this spike's public inputs via the fixed SSH helper; retrieve only APK/evidence."""
from pathlib import Path
import base64, hashlib, importlib.util, io, json, os, sys, tarfile
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
R = Path(__file__).resolve().parents[1]
helper = R.parent/'2026-11-06-asus-product-input-build-kit/scripts/remote.py'
spec = importlib.util.spec_from_file_location('fixed_remote', helper)
remote = importlib.util.module_from_spec(spec)
spec.loader.exec_module(remote)
buf = io.BytesIO()
with tarfile.open(fileobj=buf, mode='w:gz') as tar:
    for n in ['.gitignore','README.md','AndroidManifest.xml','source','assets','scripts/build.py']:
        tar.add(R/n, arcname=n)
encoded = base64.b64encode(buf.getvalue()).decode()
prefix = '/srv/android/asus-wifi-adb-apk-20261107'
verify_existing = sys.argv[1:] == ['--verify-existing']
resume = sys.argv[1:] == ['--resume'] or verify_existing
assert not sys.argv[1:] or resume
script = f'''from pathlib import Path
import base64,io,tarfile,subprocess,os
r=Path({prefix!r})
if {resume!r}:
 assert r.is_dir() and (r/'.gitignore').read_text().splitlines()[0] == '/private/'
else:
 assert not r.exists(), 'Own prefix already exists; use --resume only for this spike'
 r.mkdir(mode=0o700)
with tarfile.open(fileobj=io.BytesIO(base64.b64decode({encoded!r})),mode='r:gz') as tar:
 for m in tar.getmembers():
  assert not m.name.startswith('/') and '..' not in Path(m.name).parts and not m.issym() and not m.islnk()
 tar.extractall(r, filter='data')
p=subprocess.run(['python3','-B',str(r/'scripts/build.py')]+{(['--verify-existing'] if verify_existing else [])!r},capture_output=True,text=True,timeout=300)
print(p.stdout)
if p.returncode: raise RuntimeError(p.stderr)
'''
out = remote.run(script)
(R/'evidence/build-result.json').write_text(out)
print(out)
retrieval = remote.run(f'''from pathlib import Path
import base64,json
r=Path({prefix!r})
files=['artifacts/asus-wifi-adb-development.apk','evidence/verification.json','evidence/apksigner.txt','evidence/manifest-badging.txt','evidence/manifest-tree.txt','evidence/build-log.json']
print(json.dumps({{n:base64.b64encode((r/n).read_bytes()).decode() for n in files}}))
''')
for n,data in json.loads(retrieval).items():
    path = R/n
    path.parent.mkdir(exist_ok=True)
    path.write_bytes(base64.b64decode(data))
v=json.loads((R/'evidence/verification.json').read_text())
assert hashlib.sha256((R/'artifacts'/v['apk']['name']).read_bytes()).hexdigest() == v['apk']['sha256']
print('Retrieved signed APK and evidence; SHA-256 matches.')
