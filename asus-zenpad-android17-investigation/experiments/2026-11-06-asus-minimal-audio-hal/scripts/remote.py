#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
args=['ssh','-i',str(Path.home()/'.ssh/asus_p00a_android17'),'-o','IdentitiesOnly=yes','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','StrictHostKeyChecking=yes','-o','HostKeyAlias=compute.8549823276971553556','-o',f'UserKnownHostsFile={Path.home()}/.ssh/google_compute_known_hosts','android@IP_REDACTED','python3 -']
r=subprocess.run(args,input=Path(sys.argv[1]).read_bytes(),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
Path(sys.argv[2]).write_bytes(r.stdout)
Path(sys.argv[2]+'.stderr.txt').write_bytes(r.stderr)
print(r.stdout.decode()[:1800]); print('Saved',len(r.stdout),'bytes to',sys.argv[2]); print(r.stderr.decode(),file=sys.stderr);sys.exit(r.returncode)
