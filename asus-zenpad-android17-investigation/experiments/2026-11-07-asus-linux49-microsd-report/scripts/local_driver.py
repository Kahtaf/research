"""Use only the baseline's fixed SSH helper and this new owned prefix."""
from pathlib import Path
import importlib.util,tarfile,io,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[1]
p=R.parent/'2026-11-06-asus-stock-only-ram-rescue-build/scripts/remote.py'
spec=importlib.util.spec_from_file_location('frozen_transport',p);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
REMOTE='/srv/android/asus-linux49-microsd-report-20261107'
def call(code,data=None,timeout=180):
 p=mod.call(code,data,timeout)
 (R/'evidence/remote-last.stdout').write_bytes(p.stdout);(R/'evidence/remote-last.stderr').write_bytes(p.stderr)
 print(p.stdout.decode(errors='replace'));print(p.stderr.decode(errors='replace'),file=sys.stderr)
 if p.returncode:raise RuntimeError('Owned remote command failed')
if sys.argv[1] in ['setup','sync']:
 buf=io.BytesIO()
 with tarfile.open(fileobj=buf,mode='w') as t:
  for group in ['source','scripts','inputs']:
   for p in sorted((R/group).rglob('*')):
    if p.is_file() and '__pycache__' not in p.parts:t.add(p,arcname=str(p.relative_to(R)))
 code="""from pathlib import Path
import io,sys,tarfile,os
r=Path(REMOTE)
if SETUP:r.mkdir()
else:assert r.is_dir() and not r.is_symlink() and (r/'source/init.c').is_file()
os.chdir(r)
tarfile.open(fileobj=io.BytesIO(sys.stdin.buffer.read())).extractall(filter='data')
Path('artifacts').mkdir(exist_ok=True);Path('evidence').mkdir(exist_ok=True)
print('Owned microSD sources ready')
""".replace('REMOTE',repr(REMOTE)).replace('SETUP',repr(sys.argv[1]=='setup'))
 call(code,buf.getvalue(),30)
elif sys.argv[1]=='build':
 call("import os,runpy;os.chdir("+repr(REMOTE)+");runpy.run_path('scripts/build.py',run_name='__main__')",timeout=180)
elif sys.argv[1]=='fetch':
 code="""from pathlib import Path
import sys,tarfile
r=Path(REMOTE)
with tarfile.open(fileobj=sys.stdout.buffer,mode='w|') as t:
 for rel in ['evidence/manifest.json','evidence/build-log.json','artifacts/candidate.img']:
  p=r/rel;assert p.stat().st_size<16*1024**2;t.add(p,arcname=rel)
""".replace('REMOTE',repr(REMOTE))
 p=mod.call(code,timeout=45);assert p.returncode==0,p.stderr
 with tarfile.open(fileobj=io.BytesIO(p.stdout)) as t:t.extractall(R,filter='data')
 print('Fetched candidate and focused build evidence; padded p10 stays in owned VM prefix')
else:raise SystemExit('Use setup, build or fetch')
