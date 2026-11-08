from pathlib import Path
import importlib.util,subprocess,shlex,tarfile,io,sys,json
R=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('frozen_transport',R.parent/'2026-11-06-asus-stock-only-ram-rescue-build/scripts/remote.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
REMOTE='/srv/android/asus-minimal-ram-usb-probe-20261106'
def call(code,data=None,timeout=180):
 p=mod.call(code,data,timeout);(R/'evidence/remote-last.stdout').write_bytes(p.stdout);(R/'evidence/remote-last.stderr').write_bytes(p.stderr)
 print(p.stdout.decode(errors='replace'));print(p.stderr.decode(errors='replace'),file=sys.stderr)
 if p.returncode:raise RuntimeError('Remote command failed')
 return p.stdout
if sys.argv[1]=='setup':
 b=io.BytesIO()
 with tarfile.open(fileobj=b,mode='w') as t:
  for group in ['source','scripts','inputs']:
   for p in sorted((R/group).rglob('*')):
    if p.is_file():t.add(p,arcname=str(p.relative_to(R)))
 call("from pathlib import Path;import io,sys,tarfile,os; r=Path("+repr(REMOTE)+");r.mkdir();os.chdir(r);tarfile.open(fileobj=io.BytesIO(sys.stdin.buffer.read())).extractall(filter='data');Path('artifacts').mkdir();Path('evidence').mkdir();print('own fixture created')",b.getvalue(),30)
elif sys.argv[1]=='build':
 call("import os,runpy;os.chdir("+repr(REMOTE)+");runpy.run_path('scripts/build.py',run_name='__main__')",timeout=240)
elif sys.argv[1]=='fetch':
 code="""from pathlib import Path
import tarfile,sys
r=Path('/srv/android/asus-minimal-ram-usb-probe-20261106')
with tarfile.open(fileobj=sys.stdout.buffer,mode='w|') as t:
 for group in ['evidence','extracted']:
  for p in sorted((r/group).rglob('*')):
   if p.is_file():t.add(p,arcname=str(p.relative_to(r)))
 for n in ['candidate.img','report-fixture.fat']:
  p=r/'artifacts'/n;assert p.stat().st_size<16*1024**2;t.add(p,arcname='artifacts/'+n)
"""
 p=mod.call(code,timeout=45);assert p.returncode==0,p.stderr
 with tarfile.open(fileobj=io.BytesIO(p.stdout)) as t:t.extractall(R,filter='data')
 print('fetched small candidate and public evidence')
