"""Stage/build/fetch only this prefix using the existing product-kit SSH helper."""
from pathlib import Path
import importlib.util,tarfile,io,sys,base64,json
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('fixed_ssh',R.parent/'2026-11-06-asus-product-input-build-kit/scripts/remote.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
REMOTE='/srv/android/asus-stock-kernel-sd-rescue-20261107'
def call(code):
 try:out=m.run(code)
 except Exception as e:(R/'evidence/remote-last.stderr').write_text(str(e));raise
 (R/'evidence/remote-last.stdout').write_text(out);print(out,end='');return out
if sys.argv[1] in ('setup','update'):
 buf=io.BytesIO()
 with tarfile.open(fileobj=buf,mode='w:gz') as t:
  for group in (('source','scripts','inputs','tests') if sys.argv[1]=='setup' else ('source','scripts','tests')):
   for p in sorted((R/group).iterdir()):
    if p.is_file():t.add(p,arcname=str(p.relative_to(R)))
  for n in ['sepolicy','file_contexts.bin']:t.add(R/'artifacts'/n,arcname='artifacts/'+n)
 payload=base64.b64encode(buf.getvalue()).decode()
 call('from pathlib import Path\nimport os,io,tarfile,base64\nr=Path('+repr(REMOTE)+');'+('r.mkdir()' if sys.argv[1]=='setup' else 'assert r.is_dir()')+';os.chdir(r)\ntarfile.open(fileobj=io.BytesIO(base64.b64decode('+repr(payload)+')),mode="r:gz").extractall(filter="data")\n(r/"evidence").mkdir(exist_ok=True);print("OWNED_STOCK_COMPACT_FIXTURE_READY")')
elif sys.argv[1]=='build':call('import os,runpy;os.chdir('+repr(REMOTE)+');runpy.run_path("scripts/build.py",run_name="__main__")')
elif sys.argv[1]=='fetch':
 out=m.run('from pathlib import Path\nimport io,tarfile,base64\nr=Path('+repr(REMOTE)+');buf=io.BytesIO()\nwith tarfile.open(fileobj=buf,mode="w:gz") as t:\n for group in ("artifacts","evidence"):\n  for p in sorted((r/group).iterdir()):\n   if p.is_file() and not p.name.startswith("test_"):\n    assert p.stat().st_size<4*1024**2;t.add(p,arcname=str(p.relative_to(r)))\nprint(base64.b64encode(buf.getvalue()).decode())')
 with tarfile.open(fileobj=io.BytesIO(base64.b64decode(out)),mode='r:gz') as t:t.extractall(R,filter='data')
 print('Fetched compact real static products and focused evidence')
else:raise SystemExit('setup | build | fetch')
