from pathlib import Path
import base64,json,hashlib,os,resource
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
r=Path('/srv/android/asus-camera-arm32-route');out=[]
for n in ['abi-out/camera_abi_probe.o','abi-out/libp00a_camera_abi_probe.so','abi-out/input-pins.json','abi-out/compile.json','cpp-out/layout.cpp','cpp-out/layout.o','cpp-out/pins.json','cpp-out/commands.json']:
 p=r/n;d=p.read_bytes();assert len(d)<2*1024**2;out.append({'path':n,'bytes':len(d),'sha256':hashlib.sha256(d).hexdigest(),'base64':base64.b64encode(d).decode()})
print(json.dumps(out))
