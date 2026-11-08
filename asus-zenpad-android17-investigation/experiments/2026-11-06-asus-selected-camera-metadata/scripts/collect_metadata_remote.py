import os,resource,subprocess,sys,tarfile,io,json,hashlib
from pathlib import Path
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
r=Path('/srv/android/asus-selected-camera-metadata');r.mkdir(exist_ok=True)
rows=[]; files={}
for width in ['lib','lib64']:
 for name in ['libcam.metadata.so']:
  path='/vendor/'+width+'/'+name
  candidates=[Path('/srv/android/asus-camera-arm32-route/public')/path.strip('/').replace('/','_'),Path('/srv/android/asus-camera-source-abi-route/public')/(width+'_'+name),Path('/srv/android/asus-hardware-completeness-audit/public-selected')/(width+'_'+name)]
  old=next((p for p in candidates if p.exists()),None)
  data=old.read_bytes() if old else subprocess.run(['debugfs','-R','cat '+path,'/srv/android/asus-stock-system-backup/20261106T172146Z-89fc7700813aad85/system.img'],capture_output=True,check=True).stdout
  assert data.startswith(b'\x7fELF') and len(data)<20*1024**2,(path,len(data))
  dest=width+'_'+name;(r/dest).write_bytes(data);files[dest]=data
  rows.append({'system_path':path,'reused_copy':str(old) if old else None,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)})
files['metadata-pins.json']=json.dumps(rows,indent=2).encode()
with tarfile.open(fileobj=sys.stdout.buffer,mode='w|') as tar:
 for n,d in files.items():
  info=tarfile.TarInfo(n);info.size=len(d);tar.addfile(info,io.BytesIO(d))
