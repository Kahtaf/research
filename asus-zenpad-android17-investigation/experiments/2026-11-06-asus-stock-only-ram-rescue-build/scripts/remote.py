"""Exclusive owned builder fixture. Only existing authorized builder SSH endpoint."""
from pathlib import Path
import io,json,hashlib,subprocess,tarfile,shlex,sys
R=Path(__file__).resolve().parents[1]
REMOTE='/srv/android/2026-11-06-asus-stock-only-ram-rescue-build'
OLD='/srv/android/2026-11-06-asus-ram-original-recovery-restorer'
SSH=['ssh','-i',str(Path.home()/'.ssh/asus_p00a_android17'),'-o','IdentitiesOnly=yes','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','StrictHostKeyChecking=yes','-o','HostKeyAlias=compute.8549823276971553556','-o','UserKnownHostsFile='+str(Path.home()/'.ssh/google_compute_known_hosts'),'android@IP_REDACTED']
def call(code,data=None,timeout=None):
 return subprocess.run(SSH+['python3 -B -c '+shlex.quote(code)],input=data,capture_output=True,timeout=timeout)
def setup():
 # Input whitelist: public recovery components, tiny manifest, metadata. No SYSTEM/data.
 names=['base-header','base-kernel','base-wrapper','base-policy','core-input-metadata.json','original-stock.manifest','original-recovery.payload','file_contexts']
 oldlocal=R.parent/Path(OLD).name
 names+=['core-inputs/'+str(p.relative_to(oldlocal/'artifacts/core-inputs')) for p in (oldlocal/'artifacts/core-inputs').rglob('*') if p.is_file()]
 pins={'artifacts/'+n:hashlib.sha256((oldlocal/'artifacts'/n).read_bytes()).hexdigest() for n in names}
 # Also prove the old zero-record delivered image/full p10 and production source unchanged.
 for rel in ['artifacts/candidate/UNARMED.img','artifacts/candidate/UNARMED.p10.raw']+[str(p.relative_to(oldlocal)) for p in (oldlocal/'source').iterdir() if p.is_file()]:pins[rel]=hashlib.sha256((oldlocal/rel).read_bytes()).hexdigest()
 (R/'inputs/remote-original-pins.json').write_text(json.dumps(pins,indent=2)+'\n')
 buf=io.BytesIO()
 with tarfile.open(fileobj=buf,mode='w') as t:
  for p in R.rglob('*'):
   if p.is_file() and '__pycache__' not in str(p) and 'artifacts' not in p.relative_to(R).parts:t.add(p,arcname=str(p.relative_to(R)))
 code='''from pathlib import Path
import os,sys,tarfile,io,json,hashlib,shutil
r=Path(REMOTE);old=Path(OLD);r.mkdir();os.chdir(r)
tarfile.open(fileobj=io.BytesIO(sys.stdin.buffer.read())).extractall(filter='data')
(r/'artifacts').mkdir();(r/'evidence').mkdir(exist_ok=True);pins=json.loads((r/'inputs/remote-original-pins.json').read_text())
for rel,pin in pins.items():assert hashlib.sha256((old/rel).read_bytes()).hexdigest()==pin,rel
for name in NAMES:
 dest=r/'artifacts'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(old/'artifacts'/name,dest)
(r/'evidence/remote-inputs-before.json').write_text(json.dumps(dict(passed=True,pins=pins),indent=2)+'\\n')
print('EXCLUSIVE_OWNED_FIXTURE_READY')
'''.replace('REMOTE',repr(REMOTE)).replace('OLD',repr(OLD)).replace('NAMES',repr(names))
 p=call(code,buf.getvalue(),120)
 (R/'evidence/setup.stdout').write_bytes(p.stdout);(R/'evidence/setup.stderr').write_bytes(p.stderr)
 print(p.stdout.decode());print(p.stderr.decode(),file=sys.stderr);return p.returncode
if __name__=='__main__':sys.exit(setup())
