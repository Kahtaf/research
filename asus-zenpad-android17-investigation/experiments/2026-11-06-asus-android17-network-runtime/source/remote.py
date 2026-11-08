#!/usr/bin/env python3
import subprocess,sys
SSH=['ssh','-i','/OWNER_HOME/.ssh/asus_p00a_android17','-o','IdentitiesOnly=yes','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','StrictHostKeyChecking=yes','-o','HostKeyAlias=compute.8549823276971553556','-o','UserKnownHostsFile=/OWNER_HOME/.ssh/google_compute_known_hosts','android@IP_REDACTED']
r=subprocess.run(SSH+['bash -s'],input=sys.stdin.buffer.read())
sys.exit(r.returncode)
