from pathlib import Path
import subprocess,os,resource,hashlib,json
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
b=Path('/srv/android/lineage24');r=Path('/srv/android/asus-camera-source-abi-route')
for p in [r/'sdk37-libs/libc.so',r/'public/lib64_hw_camera.mt8163.so']:
 print('FILE',p)
 out=subprocess.run(['readelf','-Ws',str(p)],capture_output=True,text=True).stdout
 print('\n'.join(l for l in out.splitlines() if 'memcpy' in l or 'HMI' in l))
for path in ['frameworks/av/camera','system/media/camera','frameworks/native/libs/ui/include/ui/GraphicBuffer.h','hardware/interfaces/camera','frameworks/av/services/camera/libcameraservice/common']:
 p=b/path;print('PATH',p)
 if p.is_file():print(p.read_text()[:45000])
 elif p.is_dir():
  for f in p.rglob('*'):
   if f.name in ['CameraModule.cpp','CameraModule.h','Android.bp','CameraProviderInfo.cpp','CameraProviderInfo.h','CameraProviderInfoTemplated.h']:
    print('FOUND',f)
    if path in ['frameworks/av/camera','system/media/camera']:print(f.read_text()[:16000])
for path in ['frameworks/av/camera','system/media/camera','frameworks/av/media/libmedia','system/core/libnetutils','external/selinux/libselinux','system/core/fs_mgr','libnativehelper','bionic/libc/libstdc++']:
 p=b/'out/soong/.intermediates'/path;print('BUILT',p)
 if p.exists():
  hits=list(p.glob('*/*arm64*shared*/*.so'))+list(p.glob('*/*arm64*shared*/*/*.so'))
  print('\n'.join(str(x) for x in hits[:80]))
