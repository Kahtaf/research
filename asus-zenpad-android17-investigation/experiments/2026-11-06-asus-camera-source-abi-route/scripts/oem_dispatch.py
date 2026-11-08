from pathlib import Path
import subprocess,os,resource,hashlib,re,struct,json
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
r=Path('/srv/android/asus-camera-source-abi-route/public');img='/srv/android/asus-stock-system-backup/20261106T172146Z-89fc7700813aad85/system.img';llvm=Path('/srv/android/lineage24/prebuilts/clang/host/linux-x86/clang-r584948b/bin')
for name in ['libcam_platform.so','libcam.metadataprovider.so']:
 p=r/('lib64_'+name)
 if not p.exists():p.write_bytes(subprocess.run(['debugfs','-R','cat /vendor/lib64/'+name,img],capture_output=True,check=True).stdout)
 print('ELF',name,'SHA256',hashlib.sha256(p.read_bytes()).hexdigest())
 print(subprocess.run(['readelf','-dWs',str(p)],capture_output=True,text=True,check=True).stdout)
 print(subprocess.run([str(llvm/'llvm-objdump'),'-d','--demangle',str(p)],capture_output=True,text=True,check=True).stdout)
for name in ['lib64_hw_camera.mt8163.so','lib_hw_camera.mt8163.so','lib64_libcam.device3.so','lib64_libcam_platform.so']:
 p=r/name
 print('DATA AND RELOCATIONS',name)
 print(subprocess.run(['readelf','-rW','-x','.data','-x','.data.rel.ro','-x','.rodata',str(p)],capture_output=True,text=True,check=True).stdout)
print('PUBLIC CAMERA CONFIG')
for path in ['/build.prop','/vendor/build.prop']:
 data=subprocess.run(['debugfs','-R','cat '+path,img],capture_output=True,text=True).stdout
 print(path);print('\n'.join(x for x in data.splitlines() if re.search('camera|Camera|mtkcam',x)))
