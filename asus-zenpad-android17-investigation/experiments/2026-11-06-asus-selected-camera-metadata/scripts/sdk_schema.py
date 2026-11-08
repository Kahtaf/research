from pathlib import Path
import subprocess,json,base64
R=Path(__file__).resolve().parents[1]
remote="""import json,hashlib,base64,resource,os,subprocess
from pathlib import Path
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
p=Path('/srv/android/lineage24/system/media/camera/include/system/camera_metadata_tags.h');d=p.read_bytes();assert len(d)<1024**2
print(json.dumps({'path':str(p),'sha256':hashlib.sha256(d).hexdigest(),'repo_head':subprocess.run(['git','-C','/srv/android/lineage24/system/media','rev-parse','HEAD'],capture_output=True,text=True,check=True).stdout.strip(),'base64':base64.b64encode(d).decode()}))
"""
ssh=['ssh','-i',str(Path.home()/'.ssh/asus_p00a_android17'),'-o','IdentitiesOnly=yes','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','StrictHostKeyChecking=yes','-o','HostKeyAlias=compute.8549823276971553556','-o','UserKnownHostsFile='+str(Path.home()/'.ssh/google_compute_known_hosts'),'android@IP_REDACTED']
p=subprocess.run(ssh+['python3','-'],input=remote.encode(),capture_output=True,check=True);d=json.loads(p.stdout);(R/'inputs/sdk37_camera_metadata_tags.h').write_bytes(base64.b64decode(d.pop('base64')));(R/'evidence/sdk37-schema-pin.json').write_text(json.dumps(d,indent=2));print(d)
