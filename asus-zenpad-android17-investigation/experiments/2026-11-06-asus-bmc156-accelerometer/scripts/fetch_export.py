from pathlib import Path
import subprocess,tarfile,hashlib,json,io
S=Path(__file__).resolve().parents[1]
ssh=['ssh','-i',str(Path.home()/'.ssh/asus_p00a_android17'),'-o','IdentitiesOnly=yes','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','StrictHostKeyChecking=yes','-o','HostKeyAlias=compute.8549823276971553556','-o',f'UserKnownHostsFile={Path.home()}/.ssh/google_compute_known_hosts','android@IP_REDACTED']
b=subprocess.check_output(ssh+['cat /srv/android/asus-bmc156-accelerometer-r1/handoff.tar.gz'])
assert len(b)<10*1024*1024
receipt=json.loads((S/'evidence/export-receipt.json').read_text());assert len(b)==receipt['bytes'] and hashlib.sha256(b).hexdigest()==receipt['sha256']
(S/'artifacts/remote-handoff.tar.gz').write_bytes(b)
D=S/'artifacts/remote';D.mkdir(exist_ok=True)
with tarfile.open(fileobj=io.BytesIO(b),mode='r:gz') as t:
 for item in t:
  assert item.isfile() and not item.name.startswith('/') and '..' not in Path(item.name).parts
  p=D/item.name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(t.extractfile(item).read())
m=json.loads((D/'export-manifest.json').read_text());assert all(hashlib.sha256((D/p).read_bytes()).hexdigest()==h for p,h in m.items())
print('Verified compact export',len(b),'bytes',len(m),'files')
