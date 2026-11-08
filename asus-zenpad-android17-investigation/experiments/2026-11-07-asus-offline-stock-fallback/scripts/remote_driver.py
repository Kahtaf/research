"""Frozen minimal-probe SSH transport; no parent product-build operations."""
from pathlib import Path
import importlib.util,tarfile,io,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('fixed_ssh',R.parent/'2026-11-06-asus-stock-only-ram-rescue-build/scripts/remote.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
REMOTE='/srv/android/asus-offline-stock-fallback-20261107'
def call(code,data=None,timeout=240):
 p=m.call(code,data,timeout)
 (R/'evidence/remote-last.stdout').write_bytes(p.stdout);(R/'evidence/remote-last.stderr').write_bytes(p.stderr)
 print(p.stdout.decode(errors='replace'));print(p.stderr.decode(errors='replace'),file=sys.stderr)
 if p.returncode:raise RuntimeError('Owned operation failed; evidence retained')
if sys.argv[1] in ('setup','sync'):
 buf=io.BytesIO()
 with tarfile.open(fileobj=buf,mode='w') as t:
  for group in ('source','scripts','inputs'):
   for p in sorted((R/group).rglob('*')):
    if p.is_file() and '__pycache__' not in p.parts and p.name!='file_contexts.bin':t.add(p,arcname=str(p.relative_to(R)))

 code='''from pathlib import Path
import os,io,sys,tarfile
r=Path(REMOTE)
if SETUP:r.mkdir()
else:assert r.is_dir() and not r.is_symlink() and (r/'source/supervisor.c').is_file()
os.chdir(r);tarfile.open(fileobj=io.BytesIO(sys.stdin.buffer.read())).extractall(filter='data')
(r/'artifacts').mkdir(exist_ok=True);(r/'evidence').mkdir(exist_ok=True)
print('Owned SD core sources staged')
'''.replace('REMOTE',repr(REMOTE)).replace('SETUP',repr(sys.argv[1]=='setup'))
 call(code,buf.getvalue(),45)
elif sys.argv[1]=='build':call('import os,runpy;os.chdir('+repr(REMOTE)+');runpy.run_path("scripts/build.py",run_name="__main__")')
elif sys.argv[1]=='finish':call('import os,runpy,sys;os.chdir('+repr(REMOTE)+');sys.argv='+repr(sys.argv[1:])+';runpy.run_path("scripts/finish.py",run_name="__main__")')
elif sys.argv[1]=='fetch':
 code='''from pathlib import Path
import sys,tarfile
r=Path(REMOTE)
with tarfile.open(fileobj=sys.stdout.buffer,mode='w|') as t:
 for group in ('artifacts','evidence'):
  for p in sorted((r/group).iterdir()):
   if p.is_file():
    assert p.stat().st_size<16*1024**2;t.add(p,arcname=str(p.relative_to(r)))
'''.replace('REMOTE',repr(REMOTE))
 p=m.call(code,timeout=60)
 if p.returncode:raise RuntimeError(p.stderr.decode())
 with tarfile.open(fileobj=io.BytesIO(p.stdout)) as t:t.extractall(R,filter='data')
 print('Fetched own artifacts/evidence')
else:raise SystemExit('setup | sync | build | fetch')
