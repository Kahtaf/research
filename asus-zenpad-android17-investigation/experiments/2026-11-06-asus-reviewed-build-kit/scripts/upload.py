"""Copy this kit into a new isolated builder directory, never an active source tree."""
from pathlib import Path
import base64
import io
import tarfile
from remote import run
ROOT=Path(__file__).resolve().parents[1]
remote='/srv/android/asus-reviewed-build-kit/r1'
buffer=io.BytesIO()
with tarfile.open(fileobj=buffer,mode='w:gz') as tar:
    for folder in ['scripts','inputs','tests']:
        for p in sorted((ROOT/folder).rglob('*')):
            if p.is_file() and '__pycache__' not in p.parts:
                tar.add(p,arcname=str(p.relative_to(ROOT)),recursive=False)
    tar.add(ROOT/'README.md',arcname='README.md',recursive=False)
script="""from pathlib import Path
import base64,io,tarfile
r=Path(%r)
r.mkdir(parents=True,exist_ok=False)
(r/'evidence').mkdir()
with tarfile.open(fileobj=io.BytesIO(base64.b64decode(%r)),mode='r:gz') as t:
 t.extractall(r,filter='data')
print('Isolated kit uploaded:',r)
""" % (remote,base64.b64encode(buffer.getvalue()).decode())
print(run(script))
