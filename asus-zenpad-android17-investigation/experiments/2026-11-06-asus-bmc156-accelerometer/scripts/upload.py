from pathlib import Path
import subprocess,tarfile,io,sys
S=Path(__file__).resolve().parents[1]
ssh=['ssh','-i',str(Path.home()/'.ssh/asus_p00a_android17'),'-o','IdentitiesOnly=yes','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','StrictHostKeyChecking=yes','-o','HostKeyAlias=compute.8549823276971553556','-o',f'UserKnownHostsFile={Path.home()}/.ssh/google_compute_known_hosts','android@IP_REDACTED']
buf=io.BytesIO()
with tarfile.open(fileobj=buf,mode='w:gz') as t:
 for rel in sys.argv[1:]:
  p=S/rel;assert p.resolve().is_relative_to(S.resolve());t.add(p,arcname=rel)
subprocess.run(ssh+['tar xzf - -C /srv/android/asus-bmc156-accelerometer-r1'],input=buf.getvalue(),check=True)
print('uploaded',len(buf.getvalue()),'bytes')
