from pathlib import Path
import subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
BASE=['ssh','-i',str(Path.home()/'.ssh/asus_p00a_android17'),'-o','IdentitiesOnly=yes','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','StrictHostKeyChecking=yes','-o','HostKeyAlias=compute.8549823276971553556','-o','UserKnownHostsFile='+str(Path.home()/'.ssh/google_compute_known_hosts'),'android@IP_REDACTED']
if __name__=='__main__':
 if sys.argv[1]=='script':
  p=ROOT/'source'/sys.argv[2]
  r=subprocess.run(BASE+['python3 -'],input=p.read_bytes());sys.exit(r.returncode)
 else:sys.exit(subprocess.call(BASE+[sys.argv[1]]))
