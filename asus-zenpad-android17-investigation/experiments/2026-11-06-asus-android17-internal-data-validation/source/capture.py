from pathlib import Path
from remote import SSH
import subprocess,io,tarfile,hashlib,json
R=Path(__file__).resolve().parents[1]
code='''from pathlib import Path
import tarfile,sys
r=Path('/srv/android/asus-internal-data-validation')
with tarfile.open(fileobj=sys.stdout.buffer,mode='w|gz') as t:
 for p in sorted((r/'evidence').glob('*')):
  if p.is_file():t.add(p,arcname='evidence/'+p.name)
 for run in ['r1','r2']:
  for p in sorted((r/run).glob('*')):
   if p.is_file() and p.suffix in ['.json','.txt','.log','.c','.h','.py']:t.add(p,arcname='evidence/runtime-'+run+'/'+p.name)
 for name in ['payload-manifest.json','mke2fs.conf','android_filesystem_config.h','committed-android-init.rc']:
  t.add(r/'inputs'/name,arcname='inputs/'+name)
'''
b=subprocess.check_output(SSH+['python3 -'],input=code.encode());(R/'artifacts').mkdir(exist_ok=True);out=R/'artifacts/remote-evidence-r1.tar.gz';out.write_bytes(b);manifest=[]
with tarfile.open(fileobj=io.BytesIO(b),mode='r:gz') as t:
 for m in t.getmembers():
  assert m.isfile() and not Path(m.name).is_absolute() and '..' not in Path(m.name).parts
  data=t.extractfile(m).read();p=R/m.name;p.parent.mkdir(parents=True,exist_ok=True)
  if p.exists():assert p.read_bytes()==data, str(p)+' differs'
  else:p.write_bytes(data)
  manifest.append(dict(path=m.name,bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
(R/'evidence/capture-verification.json').write_text(json.dumps(dict(archive=str(out),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b),files=manifest,passed=True),indent=2)+'\n');print(len(b),len(manifest),hashlib.sha256(b).hexdigest())
