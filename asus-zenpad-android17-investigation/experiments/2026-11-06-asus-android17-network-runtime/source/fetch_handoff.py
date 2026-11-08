from pathlib import Path
import subprocess,tarfile,hashlib
SSH=['ssh','-i','/OWNER_HOME/.ssh/asus_p00a_android17','-o','IdentitiesOnly=yes','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','StrictHostKeyChecking=yes','-o','HostKeyAlias=compute.8549823276971553556','-o','UserKnownHostsFile=/OWNER_HOME/.ssh/google_compute_known_hosts','android@IP_REDACTED']
R=Path(__file__).resolve().parents[1];archive=R/'artifacts/handoff-r1.tar'
with archive.open('wb') as out:subprocess.run(SSH+['tar -C /srv/android/asus-network-runtime -cf - handoff-r1'],stdout=out,check=True)
with tarfile.open(archive) as t:t.extractall(R/'artifacts',filter='data')
print('handoff archive',archive.stat().st_size,hashlib.sha256(archive.read_bytes()).hexdigest())
