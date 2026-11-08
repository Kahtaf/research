from pathlib import Path
import importlib.util,subprocess,shlex,tarfile,io,sys,json
R=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('frozen_transport',R.parent/'2026-11-06-asus-stock-only-ram-rescue-build/scripts/remote.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
REMOTE='/srv/android/asus-linux49-minimal-ram-probe-20261106'
def call(code,data=None,timeout=180):
 p=mod.call(code,data,timeout);(R/'evidence/remote-last.stdout').write_bytes(p.stdout);(R/'evidence/remote-last.stderr').write_bytes(p.stderr)
 print(p.stdout.decode(errors='replace'));print(p.stderr.decode(errors='replace'),file=sys.stderr)
 if p.returncode:raise RuntimeError('Remote command failed')
 return p.stdout
if sys.argv[1] in ['setup','sync']:
 b=io.BytesIO()
 with tarfile.open(fileobj=b,mode='w') as t:
  for group in ['source','scripts','inputs']:
   for p in sorted((R/group).rglob('*')):
    if p.is_file() and '__pycache__' not in p.parts:t.add(p,arcname=str(p.relative_to(R)))
 code="""from pathlib import Path
import io,sys,tarfile,os,shutil
r=Path(REMOTE)
if SETUP:r.mkdir()
else:assert r.is_dir() and not r.is_symlink() and (r/'source/init.c').is_file()
os.chdir(r)
for p in r.rglob('__pycache__'):
 assert r in p.resolve().parents;shutil.rmtree(p)
tarfile.open(fileobj=io.BytesIO(sys.stdin.buffer.read())).extractall(filter='data')
Path('artifacts').mkdir(exist_ok=True);Path('evidence').mkdir(exist_ok=True)
print('own fixture staged')
""".replace('REMOTE',repr(REMOTE)).replace('SETUP',repr(sys.argv[1]=='setup'))
 call(code,b.getvalue(),30)
elif sys.argv[1]=='build':
 call("import os,runpy;os.chdir("+repr(REMOTE)+");runpy.run_path('scripts/build.py',run_name='__main__')",timeout=240)
elif sys.argv[1]=='fetch':
 code="""from pathlib import Path
import tarfile,sys
r=Path('/srv/android/asus-linux49-minimal-ram-probe-20261106')
with tarfile.open(fileobj=sys.stdout.buffer,mode='w|') as t:
 for group in ['evidence']:
  for p in sorted((r/group).rglob('*')):
   if p.is_file():t.add(p,arcname=str(p.relative_to(r)))
 for n in ['candidate.img','report-fixture.fat']:
  p=r/'artifacts'/n;assert p.stat().st_size<16*1024**2;t.add(p,arcname='artifacts/'+n)
"""
 p=mod.call(code,timeout=45);assert p.returncode==0,p.stderr
 with tarfile.open(fileobj=io.BytesIO(p.stdout)) as t:t.extractall(R,filter='data')
 print('fetched small candidate and public evidence')
