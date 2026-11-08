from pathlib import Path
b=Path('/srv/android/lineage24')
for rel in ['out/soong/.intermediates/bionic/libc/libc','out/soong/.intermediates/frameworks/native/libs/ui/libui','out/soong/.intermediates/system/media/camera/libcamera_metadata','out/soong/.intermediates/bionic/libc/crtbegin_so']:
 p=b/rel;print(rel,[x.name for x in p.iterdir()] if p.exists() else 'MISSING')
for base in [Path('/srv/android/asus-sdk37-graphics-abi-bridge'),Path('/srv/android/asus-minimal-audio-hal-20261106')]:
 print('FIXTURE',base,base.exists())
print('SCRATCH',[x.name for x in Path('/srv/android').iterdir() if any(s in x.name for s in ['graphic','abi','compat'])])
