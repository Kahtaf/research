from pathlib import Path
import subprocess,os,resource,re,hashlib,json
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
r=Path('/srv/android/asus-camera-source-abi-route');b=Path('/srv/android/lineage24');img='/srv/android/asus-stock-system-backup/20261106T172146Z-89fc7700813aad85/system.img';rows=[]
for name in ['libarcsoft3DNR.so','libarcsoftFace.so','libarcsoftHDR.so','libarcsoftNightHawk.so','libarcsoftStabilizer.so','libstdc++.so']:
 path='/lib64/'+name;data=subprocess.run(['debugfs','-R','cat '+path,img],capture_output=True,check=True).stdout
 if not data.startswith(b'\x7fELF'):rows.append({'path':path,'missing':True});continue
 assert len(data)<12*1024**2
 p=r/'inspect-temp.so';p.write_bytes(data);elf=subprocess.run(['readelf','-dW','--dyn-syms',str(p)],capture_output=True,text=True,check=True).stdout;p.unlink()
 rows.append({'path':path,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'elf':elf})
print('PUBLIC_SYSTEM_LEAVES',json.dumps(rows))
root=b/'kernel/asus/p00a-fd'
for sub in ['drivers/misc/mediatek/imgsensor','drivers/staging/android/ion','drivers/misc/mediatek/ion']:
 p=root/sub
 if not p.exists():continue
 for f in p.rglob('*'):
  if f.name in ['kd_sensorlist.c','kd_camera_hw.c','ion_drv.h','mtk_ion.h']:
   data=f.read_bytes();print('SOURCE',f,'SHA256',hashlib.sha256(data).hexdigest())
   text=data.decode(errors='replace');matches=[(i,l) for i,l in enumerate(text.splitlines(),1) if re.search(r'^(static )?(long|int).*Ioctl|FEATURECONCTROL|FeatureId|compat_ioctl|copy_from_user|ION_SYS|ION_MM|ION_CMD|struct ion_',l)]
   print('\n'.join(f'{i}: {l}' for i,l in matches[:90]))
print('SENSOR HEADER')
p=b/'frameworks/native/libs/sensor/include/sensor/SensorManager.h'
if p.exists():
 print(str(p),'SHA256',hashlib.sha256(p.read_bytes()).hexdigest());print('\n'.join(f'{i}: {l}' for i,l in enumerate(p.read_text().splitlines(),1) if re.search('getInstanceForPackage|createEventQueue|getDefaultSensor',l)))
