"""Resume audit only after finished native handle; never rerun assembly."""
from remote import R,REMOTE,call
import io,tarfile,sys
buf=io.BytesIO()
with tarfile.open(fileobj=buf,mode='w') as t:
 for p in (R/'scripts').glob('*.py'):t.add(p,arcname='scripts/'+p.name)
code='''from pathlib import Path
import sys,io,tarfile
r=Path(REMOTE);archive=tarfile.open(fileobj=io.BytesIO(sys.stdin.buffer.read()))
for m in archive.getmembers():
 p=r/m.name
 if p.exists() and p.read_bytes()!=archive.extractfile(m).read():
  dest=r/'revisions/postflight-r1'/m.name;dest.parent.mkdir(parents=True,exist_ok=True)
  assert not dest.exists();dest.write_bytes(p.read_bytes())
archive.extractall(r,filter='data')
'''.replace('REMOTE',repr(REMOTE))
p=call(code,buf.getvalue());assert p.returncode==0,p.stderr
p=call('import runpy;runpy.run_path('+repr(REMOTE+'/scripts/postflight.py')+',run_name="__main__")')
(R/'evidence/postflight-r2.stdout').write_bytes(p.stdout);(R/'evidence/postflight-r2.stderr').write_bytes(p.stderr)
print(p.stdout.decode());print(p.stderr.decode(),file=sys.stderr);sys.exit(p.returncode)
