import subprocess, sys
SSH=['ssh','-i',__import__('os').path.expanduser('~/.ssh/asus_p00a_android17'),'-o','IdentitiesOnly=yes','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','StrictHostKeyChecking=yes','-o','HostKeyAlias=compute.8549823276971553556','-o','UserKnownHostsFile='+__import__('os').path.expanduser('~/.ssh/google_compute_known_hosts'),'android@IP_REDACTED']
if __name__=='__main__':
    sys.exit(subprocess.call(SSH+[sys.argv[1]]))
