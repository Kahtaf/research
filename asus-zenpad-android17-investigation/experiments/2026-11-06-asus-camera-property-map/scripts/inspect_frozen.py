from pathlib import Path
import hashlib,subprocess,json
r=Path('/srv/android/asus-camera-property-map-20261106')
f=Path('/srv/android/asus-camera-arm32-route/cpp-out/sdk37')
files=['system/core/libutils/include/utils/'+x+'.h' for x in ['String8','VectorImpl','SortedVector','KeyedVector','TypeHelpers']]
for rel in files:
 p=f/rel;d=p.read_bytes();print('FILE',p,'SHA256',hashlib.sha256(d).hexdigest());print(d.decode())
clang=Path('/srv/android/lineage24/prebuilts/clang/host/linux-x86/clang-r584948b/bin')
for name in ['asus-camera-arm32-route','asus-camera-source-abi-route']:
 b=Path('/srv/android')/name
 p=b/'sdk37-libs/libutils.so'
 print('PROVIDER',p,hashlib.sha256(p.read_bytes()).hexdigest())
 out=subprocess.run([str(clang/'llvm-readelf'),'-h','-d','--dyn-syms','-W',str(p)],capture_output=True,text=True,check=True).stdout
 (r/(name+'-libutils.txt')).write_text(out)
 print('\n'.join(l for l in out.splitlines() if any(s in l for s in ['NEEDED','VectorImplC','VectorImplD','VectorImpl13finish','String8C','String8D','String8aS'])))
p=Path('/srv/android/asus-camera-arm32-route/public/vendor_lib_libcam_utils.so')
out=subprocess.run([str(clang/'llvm-readelf'),'--dyn-syms','-W',str(p)],capture_output=True,text=True,check=True).stdout
print('OEM_IMPORTS',hashlib.sha256(p.read_bytes()).hexdigest(),'\n'+'\n'.join(l for l in out.splitlines() if 'PropertyMap' in l))
