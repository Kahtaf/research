"""Use only the existing fixed SSH helper; stage/build/fetch this owned fixture."""
from pathlib import Path
import importlib.util,tarfile,io,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('fixed_ssh',R.parent/'2026-11-06-asus-stock-only-ram-rescue-build/scripts/remote.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
REMOTE='/srv/android/asus-sd-media-flag-core-20261107'
def call(code,data=None,timeout=180):
 p=m.call(code,data,timeout)
 (R/'evidence/remote-last.stdout').write_bytes(p.stdout);(R/'evidence/remote-last.stderr').write_bytes(p.stderr)
 print(p.stdout.decode(errors='replace'));print(p.stderr.decode(errors='replace'),file=sys.stderr)
 if p.returncode:raise RuntimeError('Owned operation failed; evidence retained')
if sys.argv[1]=='setup':
 buf=io.BytesIO()
 with tarfile.open(fileobj=buf,mode='w') as t:
  for group in ('source','scripts','inputs','tests'):
   for p in sorted((R/group).rglob('*')):
    if p.is_file() and '__pycache__' not in p.parts:t.add(p,arcname=str(p.relative_to(R)))
  for n in ['sepolicy','file_contexts.bin']:t.add(R/'artifacts'/n,arcname='artifacts/'+n)
 code="""from pathlib import Path
import os,io,sys,tarfile
r=Path(REMOTE);r.mkdir();os.chdir(r)
tarfile.open(fileobj=io.BytesIO(sys.stdin.buffer.read())).extractall(filter='data')
(r/'evidence').mkdir();print('OWNED_COMPACT_FIXTURE_READY')
""".replace('REMOTE',repr(REMOTE))
 call(code,buf.getvalue(),45)
elif sys.argv[1]=='build':call('import os,runpy;os.chdir('+repr(REMOTE)+');runpy.run_path("scripts/build.py",run_name="__main__")')
elif sys.argv[1]=='fetch':
 code="""from pathlib import Path
import sys,tarfile
r=Path(REMOTE)
with tarfile.open(fileobj=sys.stdout.buffer,mode='w|') as t:
 for group in ('artifacts','evidence'):
  for p in sorted((r/group).iterdir()):
   if p.is_file() and p.name!='test_sd_binding':
    assert p.stat().st_size<4*1024**2;t.add(p,arcname=str(p.relative_to(r)))
""".replace('REMOTE',repr(REMOTE))
 p=m.call(code,timeout=60)
 if p.returncode:raise RuntimeError(p.stderr.decode())
 with tarfile.open(fileobj=io.BytesIO(p.stdout)) as t:t.extractall(R,filter='data')
 print('Fetched compact products and focused build evidence')
else:raise SystemExit('setup | build | fetch')
