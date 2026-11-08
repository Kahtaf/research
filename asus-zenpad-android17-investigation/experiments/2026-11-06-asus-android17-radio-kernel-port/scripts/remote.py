#!/usr/bin/env python3
"""Commands are restricted by caller to the isolated radio fixture."""
import pathlib, subprocess, sys
SSH=['ssh','-i',str(pathlib.Path.home()/'.ssh/asus_p00a_android17'),'-o','IdentitiesOnly=yes','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','StrictHostKeyChecking=yes','-o','HostKeyAlias=compute.8549823276971553556','-o','UserKnownHostsFile='+str(pathlib.Path.home()/'.ssh/google_compute_known_hosts'),'android@IP_REDACTED']
if __name__=='__main__':
 sys.exit(subprocess.call(SSH+[sys.argv[1]]))
