import remote,json
from pathlib import Path
s=r'''
from pathlib import Path
import hashlib,json
A=Path('/srv/android/lineage24');R=Path('/srv/android/asus-reviewed-build-kit/r8')
def info(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return dict(bytes=p.stat().st_size,sha256=h.hexdigest())
paths=[p for p in (A/'.repo').rglob('*') if p.is_file() and p.stat().st_size<2000000]
print(json.dumps(dict(repo_files=[str(p.relative_to(A)) for p in paths],repo_relevant={str(p.relative_to(A)):p.read_text(errors='replace') for p in paths if any(x in p.name.lower() for x in ['manifest','receipt','source','archive'])},webview={str(p.relative_to(A)):p.read_text() for p in [A/'external/chromium-webview/.gitattributes',A/'external/chromium-webview/Android.bp'] if p.exists()},attempt={str(p.relative_to(R)):info(p) for p in (R/'attempt').rglob('*') if p.is_file()},failed=(R/'attempt/native-evidence/bootimage/siso_failed_commands.sh').read_text(),terminal={p.name:p.read_text() for p in Path('/srv/android/asus-device-product/logs').glob('full-build-r8.*') if p.suffix in ['.finished','.exit-code']},own_collision={str(p):p.exists() for p in [Path('/srv/android/asus-reviewed-build-kit/r9'),Path('/srv/android/asus-product-integration-staging/r9'),Path('/srv/android/asus-reviewed-build-kit/r9-fixtures')]}),indent=2))
'''
r=remote.run(s);Path('2026-11-06-asus-r9-webview-continuation/evidence/initial.json').write_text(r)
d=json.loads(r);print(json.dumps({k:v for k,v in d.items() if k not in ['attempt','repo_relevant']},indent=2));print(json.dumps(d['repo_relevant'],indent=2)[:13000])
