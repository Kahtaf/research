from pathlib import Path
import subprocess,tarfile,io
s=Path(__file__).resolve().parents[1]
buf=io.BytesIO()
with tarfile.open(fileobj=buf,mode='w:gz') as t:
 for rel in ['src','tests','staging','scripts/compile_remote.py','evidence/audio-default-commands.txt','evidence/tinyalsa-inputs.txt','source/sdk37/external/tinyalsa_new']:
  p=s/rel
  if p.exists():t.add(p,arcname=rel)
args=['ssh','-i',str(Path.home()/'.ssh/asus_p00a_android17'),'-o','IdentitiesOnly=yes','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','StrictHostKeyChecking=yes','-o','HostKeyAlias=compute.8549823276971553556','-o',f'UserKnownHostsFile={Path.home()}/.ssh/google_compute_known_hosts','android@IP_REDACTED','tar -xzf - -C /srv/android/asus-minimal-audio-hal-20261106']
subprocess.run(args,input=buf.getvalue(),check=True)
print('Uploaded public owned fixture',len(buf.getvalue()),'bytes')
