import os, subprocess, sys
SSH=['ssh','-i',os.path.expanduser('~/.ssh/asus_p00a_android17'),'-o','IdentitiesOnly=yes','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','StrictHostKeyChecking=yes','-o','HostKeyAlias=compute.8549823276971553556','-o','UserKnownHostsFile='+os.path.expanduser('~/.ssh/google_compute_known_hosts'),'android@IP_REDACTED']
if __name__=='__main__':
    result=subprocess.run(SSH+[sys.argv[1]],input=sys.stdin.buffer.read())
    sys.exit(result.returncode)
