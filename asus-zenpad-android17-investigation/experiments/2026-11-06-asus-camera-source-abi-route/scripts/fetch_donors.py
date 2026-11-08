from pathlib import Path
import urllib.request, json, base64, hashlib
root=Path(__file__).resolve().parents[1]/'donors'; root.mkdir(exist_ok=True)
tag='android-9.0.0_r61'
sets={
'frameworks/av':['services/camera/libcameraservice/api1/CameraClient.cpp','services/camera/libcameraservice/api1/CameraClient.h','services/camera/libcameraservice/device1/CameraHardwareInterface.cpp','services/camera/libcameraservice/device1/CameraHardwareInterface.h','services/camera/libcameraservice/common/CameraProviderManager.cpp','services/camera/libcameraservice/common/CameraProviderManager.h','services/camera/libcameraservice/CameraService.cpp','services/camera/libcameraservice/Android.mk'],
'frameworks/base':['core/java/android/hardware/camera2/CameraManager.java','core/jni/android_hardware_camera2_legacy_LegacyCameraDevice.cpp','core/jni/android_hardware_camera2_legacy_PerfMeasurement.cpp','core/jni/Android.bp'],
}
receipts=[]
def get(url):
 with urllib.request.urlopen(url,timeout=25) as f:return f.read(4*1024**2)
for repo,paths in sets.items():
 url=f'https://android.googlesource.com/platform/{repo}/+/{tag}?format=JSON'
 commit=json.loads(get(url).decode().removeprefix(")]}'\n"))['commit']
 if repo=='frameworks/base':
  d='core/java/android/hardware/camera2/legacy/'
  entries=json.loads(get(f'https://android.googlesource.com/platform/{repo}/+/{commit}/{d}?format=JSON').decode().removeprefix(")]}'\n"))['entries']
  paths.extend(d+e['name'] for e in entries if e['type']=='blob' and e['name'].endswith('.java'))
 for path in paths:
  url=f'https://android.googlesource.com/platform/{repo}/+/{commit}/{path}'
  dest=root/repo/path;dest.parent.mkdir(parents=True,exist_ok=True)
  if dest.exists():data=dest.read_bytes()
  else:data=base64.b64decode(get(url+'?format=TEXT'));dest.write_bytes(data)
  receipts.append({'tag':tag,'commit':commit,'path':repo+'/'+path,'url':url,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
  print(repo,path,len(data),flush=True)
 (root/'pins.json').write_text(json.dumps(receipts,indent=2)+'\n')
