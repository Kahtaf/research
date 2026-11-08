from pathlib import Path
import subprocess,base64,json,tarfile,hashlib,io
L=Path(__file__).resolve().parents[1];H=Path.home();R='/srv/android/asus-firstboot-parity-continuation'
SSH=['ssh','-i',str(H/'.ssh/asus_p00a_android17'),'-o','IdentitiesOnly=yes','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','StrictHostKeyChecking=yes','-o','HostKeyAlias=compute.8549823276971553556','-o','UserKnownHostsFile='+str(H/'.ssh/google_compute_known_hosts'),'android@IP_REDACTED']
files={p.name:base64.b64encode(p.read_bytes()).decode() for p in (L/'scripts').glob('*.py') if p.name!='remote.py'}
code="from pathlib import Path\nimport base64,json\nr=Path("+repr(R)+")/'source/continuation';r.mkdir(exist_ok=True)\nfor n,b in "+repr(files)+".items(): (r/n).write_bytes(base64.b64decode(b))\n"
subprocess.run(SSH+['python3 -'],input=code.encode(),check=True)
code=r'''
from pathlib import Path
import tarfile,sys,json,hashlib,io
R=Path('/srv/android/asus-firstboot-parity-continuation')
p=json.loads((R/'evidence/preflight.json').read_text());p['processes']=[l for l in p['processes'].splitlines() if 'prebuilts/siso/linux-x86/siso ' in l];(R/'evidence/preflight-summary.json').write_text(json.dumps(p,indent=2))
files=[]
for sub in ['source','evidence']:
 files += [p for p in (R/sub).rglob('*') if p.is_file() and p.name not in ['preflight.json','export-manifest.json']]
for name in ['run-cpuset-r3','run-locks-r1','run-locks-r2','run-policy-r4','run-boot-r11']:
 files += [p for p in (R/name).iterdir() if p.is_file() and p.suffix in ['.json','.log','.c','.py']]
manifest={p.relative_to(R).as_posix():{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(files)}
(R/'evidence/export-manifest.json').write_text(json.dumps(manifest,indent=2));files.append(R/'evidence/export-manifest.json')
with tarfile.open(fileobj=sys.stdout.buffer,mode='w|gz') as tf:
 for p in sorted(set(files)):tf.add(p,arcname=p.relative_to(R).as_posix(),recursive=False)
'''
result=subprocess.run(SSH+['python3 -'],input=code.encode(),capture_output=True,check=True)
archive=L/'artifacts/evidence-r3.tar.gz';archive.write_bytes(result.stdout)
dst=L/'artifacts/frozen-r3';dst.mkdir(exist_ok=True)
with tarfile.open(fileobj=io.BytesIO(result.stdout),mode='r:gz') as tf: tf.extractall(dst,filter='data')
manifest=json.loads((dst/'evidence/export-manifest.json').read_text())
for n,v in manifest.items():
 p=dst/n; assert p.stat().st_size==v['bytes'];assert hashlib.sha256(p.read_bytes()).hexdigest()==v['sha256'],n
receipt={'files_verified':len(manifest),'archive_bytes':len(result.stdout),'archive_sha256':hashlib.sha256(result.stdout).hexdigest(),'all_passed':True}
(L/'evidence/export-verification-r3.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt))
