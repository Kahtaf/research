#!/usr/bin/env python3
import subprocess,sys
SSH=['ssh','-i','/OWNER_HOME/.ssh/asus_p00a_android17','-o','IdentitiesOnly=yes','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','StrictHostKeyChecking=yes','-o','HostKeyAlias=compute.8549823276971553556','-o','UserKnownHostsFile=/OWNER_HOME/.ssh/google_compute_known_hosts','android@IP_REDACTED']

import subprocess,sys
from pathlib import Path
p=Path(sys.argv[1]); assert p.is_file()
dest='/srv/android/asus-network-runtime/source/'+p.name
subprocess.run(SSH+['cat > '+dest],input=p.read_bytes(),check=True)
