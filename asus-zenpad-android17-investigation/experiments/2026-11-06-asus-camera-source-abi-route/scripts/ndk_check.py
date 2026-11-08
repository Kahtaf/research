from pathlib import Path
import hashlib,os,resource,re
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
r=Path('/srv/android/lineage24/frameworks/av/camera/ndk')
for p in r.rglob('*CameraManager*.cpp'):
 print('FILE',p,'SHA256',hashlib.sha256(p.read_bytes()).hexdigest());lines=p.read_text().splitlines();wanted=set()
 for i,l in enumerate(lines):
  if re.search('LEGACY|HAL1|BACKWARD_COMPATIBLE|connectDevice|supportsCameraApi|hardwareLevel|getCameraIdList',l):wanted.update(range(max(0,i-5),min(len(lines),i+10)))
 print('\n'.join(f'{i+1}: {lines[i]}' for i in sorted(wanted)))
