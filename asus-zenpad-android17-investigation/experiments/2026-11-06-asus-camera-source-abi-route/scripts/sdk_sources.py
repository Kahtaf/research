from pathlib import Path
import hashlib,json,os,resource
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
b=Path('/srv/android/lineage24');r=Path('/srv/android/asus-camera-source-abi-route/sdk37')
paths=[
'frameworks/av/services/camera/libcameraservice/CameraService.cpp',
'frameworks/av/services/camera/libcameraservice/CameraService.h',
'frameworks/av/services/camera/libcameraservice/Android.bp',
'frameworks/av/services/camera/libcameraservice/common/hidl/HidlProviderInfo.cpp',
'frameworks/av/services/camera/libcameraservice/common/hidl/HidlProviderInfo.h',
'frameworks/av/services/camera/libcameraservice/common/CameraProviderManager.cpp',
'frameworks/av/services/camera/libcameraservice/common/CameraProviderManager.h',
'frameworks/av/services/camera/libcameraservice/common/CameraProviderInfo.cpp',
'frameworks/base/core/java/android/hardware/camera2/CameraManager.java',
'frameworks/base/core/jni/android_hardware_Camera.cpp',
'hardware/interfaces/camera/provider/2.4/default/LegacyCameraProviderImpl_2_4.cpp',
'hardware/interfaces/camera/provider/2.4/default/Android.bp',
'hardware/interfaces/camera/common/1.0/default/CameraModule.cpp',
'hardware/interfaces/camera/device/1.0/default/CameraDevice.cpp',
'hardware/interfaces/camera/device/3.2/default/CameraDevice.cpp',
'hardware/interfaces/camera/device/3.2/default/CameraDeviceSession.cpp',
'hardware/interfaces/camera/device/1.0/ICameraDevice.hal',
'hardware/interfaces/camera/provider/2.4/ICameraProvider.hal',
'hardware/libhardware/include_all/hardware/camera_common.h',
'hardware/libhardware/include_all/hardware/camera.h',
'hardware/libhardware/include_all/hardware/camera3.h',
'hardware/libhardware/include_all/hardware/hardware.h']
res=[]
for p in paths:
 f=b/p
 if not f.is_file():res.append({'path':p,'missing':True});continue
 data=f.read_bytes();assert len(data)<1024**2
 dest=r/p;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
 res.append({'path':p,'sha256':hashlib.sha256(data).hexdigest(),'text':data.decode()})
print(json.dumps(res))
