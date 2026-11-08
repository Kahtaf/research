from pathlib import Path
import subprocess,sys
SSH=['ssh','-i',str(Path.home()/'.ssh/asus_p00a_android17'),'-o','IdentitiesOnly=yes','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','StrictHostKeyChecking=yes','-o','HostKeyAlias=compute.8549823276971553556','-o','UserKnownHostsFile='+str(Path.home()/'.ssh/google_compute_known_hosts'),'android@IP_REDACTED']
if __name__=='__main__':
 p=subprocess.run(SSH+['python3 -'],input=Path(sys.argv[1]).read_bytes());sys.exit(p.returncode)
