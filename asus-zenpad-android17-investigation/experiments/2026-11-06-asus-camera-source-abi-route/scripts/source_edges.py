from pathlib import Path
import os,resource,hashlib,json,subprocess,re
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
b=Path('/srv/android/lineage24');r=Path('/srv/android/asus-camera-source-abi-route/sdk37')
paths=['hardware/interfaces/camera/common/default/CameraModule.cpp','hardware/interfaces/camera/common/default/include/CameraModule.h','frameworks/av/services/camera/libcameraservice/common/CameraProviderInfoTemplated.h','frameworks/av/camera/aidl/android/hardware/ICameraService.aidl','frameworks/av/camera/aidl/android/hardware/camera2/ICameraDeviceUser.aidl','frameworks/av/camera/aidl/android/hardware/camera2/ICameraDeviceCallbacks.aidl','frameworks/av/camera/aidl/android/hardware/ICamera.aidl']
k=b/'kernel/asus/p00a-fd/drivers/misc/mediatek'
for sub in ['imgsensor','cameraisp','cam_cal','m4u','ion']:
 p=k/sub
 if p.exists():
  for f in p.rglob('*'):
   if f.name in ['kd_imgsensor.h','kd_imgsensor_define.h','camera_isp.h','camera_isp_FrmB.h','cam_cal.h','ion_drv.h','mtk_ion.h','m4u.h','m4u_priv.h','m4u_port.h'] and (sub!='cameraisp' or '/mt8163/' in str(f)):
    paths.append(str(f.relative_to(b)))
res=[]
for path in paths:
 p=b/path
 if not p.is_file():res.append({'path':path,'missing':True});continue
 data=p.read_bytes();dest=r/path;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
 res.append({'path':path,'sha256':hashlib.sha256(data).hexdigest(),'text':data.decode()})
print(json.dumps(res))
