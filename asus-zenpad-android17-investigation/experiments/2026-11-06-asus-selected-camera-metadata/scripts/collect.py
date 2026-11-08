from pathlib import Path
import subprocess,json,hashlib
root=Path(__file__).resolve().parents[1]
ssh=['ssh','-i',str(Path.home()/'.ssh/asus_p00a_android17'),'-o','IdentitiesOnly=yes','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','StrictHostKeyChecking=yes','-o','HostKeyAlias=compute.8549823276971553556','-o','UserKnownHostsFile='+str(Path.home()/'.ssh/google_compute_known_hosts'),'android@IP_REDACTED']
remote='''import os,resource,subprocess,sys,tarfile,io,json,hashlib
from pathlib import Path
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
r=Path('/srv/android/asus-selected-camera-metadata');r.mkdir(exist_ok=True)
rows=[]; files={}
for width in ['lib','lib64']:
 for name in ['libcam.metadataprovider.so','libcam.halsensor.so','libcam.hal3a.v3.so','libcameracustom.so']:
  path='/vendor/'+width+'/'+name
  candidates=[Path('/srv/android/asus-camera-arm32-route/public')/path.strip('/').replace('/','_'),Path('/srv/android/asus-camera-source-abi-route/public')/(width+'_'+name),Path('/srv/android/asus-hardware-completeness-audit/public-selected')/(width+'_'+name)]
  old=next((p for p in candidates if p.exists()),None)
  data=old.read_bytes() if old else subprocess.run(['debugfs','-R','cat '+path,'/srv/android/asus-stock-system-backup/20261106T172146Z-89fc7700813aad85/system.img'],capture_output=True,check=True).stdout
  assert data.startswith(b'\\x7fELF') and len(data)<20*1024**2,(path,len(data))
  dest=width+'_'+name;(r/dest).write_bytes(data);files[dest]=data
  rows.append({'system_path':path,'reused_copy':str(old) if old else None,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)})
files['elf-pins.json']=json.dumps(rows,indent=2).encode()
with tarfile.open(fileobj=sys.stdout.buffer,mode='w|') as tar:
 for n,d in files.items():
  info=tarfile.TarInfo(n);info.size=len(d);tar.addfile(info,io.BytesIO(d))
'''
(root/'scripts/collect_remote.py').write_text(remote)
r=subprocess.run(ssh+['python3','-'],input=remote.encode(),capture_output=True,check=True)
import tarfile,io
with tarfile.open(fileobj=io.BytesIO(r.stdout)) as tar:
 for m in tar:
  assert '/' not in m.name
  (root/'inputs'/m.name).write_bytes(tar.extractfile(m).read())
print((root/'inputs/elf-pins.json').read_text())
