from pathlib import Path
import subprocess,os,resource,hashlib,json,re
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
r=Path('/srv/android/asus-camera-source-abi-route');r.mkdir(exist_ok=True);(r/'public').mkdir(exist_ok=True)
img='/srv/android/asus-stock-system-backup/20261106T172146Z-89fc7700813aad85/system.img'
llvm=Path('/srv/android/lineage24/prebuilts/clang/host/linux-x86/clang-r584948b/bin')
print('LLVM',llvm,llvm.exists())
for arch in ['lib64','lib']:
 for name in ['hw/camera.mt8163.so','libcam.device1.so','libcam.device3.so','libcam.metadataprovider.so','libcam3_hwpipeline.so','libcam3_app.so']:
  path='/vendor/'+arch+'/'+name
  old=Path('/srv/android/asus-hardware-completeness-audit/public-selected')/(arch+'_'+name.replace('/','_'))
  data=old.read_bytes() if old.exists() else subprocess.run(['debugfs','-R','cat '+path,img],capture_output=True,check=True).stdout
  assert data.startswith(b'\x7fELF') and len(data)<1024**2
  dest=r/'public'/(arch+'_'+name.replace('/','_'));dest.write_bytes(data)
  print('\nELF',path,'SIZE',len(data),'SHA256',hashlib.sha256(data).hexdigest())
  out=subprocess.run(['readelf','-dWs',str(dest)],capture_output=True,text=True,check=True).stdout
  print(out)
  strings=[s.decode() for s in re.findall(rb'[\x20-\x7e]{5,}',data)]
  print('SELECTED STRINGS',json.dumps([s for s in strings if re.search(r'hal3|HAL3|[Vv]ersion|device3|[Cc]reat|[Oo]pen|[Cc]amera|[Pp]roperty',s)]))
  if arch=='lib64' and name in ['hw/camera.mt8163.so','libcam.device3.so']:
   print('DISASSEMBLY');print(subprocess.run([str(llvm/'llvm-objdump'),'-d','--demangle',str(dest)],capture_output=True,text=True,check=True).stdout)
