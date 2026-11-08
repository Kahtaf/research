from pathlib import Path
import os,resource,subprocess,hashlib,json,re
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
r=Path('/srv/android/asus-camera-arm32-route');b=Path('/srv/android/lineage24');img='/srv/android/asus-stock-system-backup/20261106T172146Z-89fc7700813aad85/system.img';p=r/'public/lib_libutils.so'
d=subprocess.run(['debugfs','-R','cat /lib/libutils.so',img],capture_output=True,check=True).stdout;assert len(d)<1024**2;p.write_bytes(d)
print('OEM_LIBUTILS_SHA256',hashlib.sha256(d).hexdigest())
e=subprocess.run(['readelf','--dyn-syms','-W',p],capture_output=True,text=True,check=True).stdout
print('\n'.join(l for l in e.splitlines() if 'PropertyMap' in l))
dis=subprocess.run([str(b/'prebuilts/clang/host/linux-x86/clang-r584948b/bin/llvm-objdump'),'-d','--demangle','--triple=thumbv7-linux-android','-j','.text',p],capture_output=True,text=True,check=True).stdout
lines=dis.splitlines();keep=set()
for i,l in enumerate(lines):
 if re.match(r'^[0-9a-f]+ <',l) and any(s in l for s in ['PropertyMap::PropertyMap','PropertyMap::~PropertyMap','PropertyMap::clear()','PropertyMap::hasProperty']):
  end=next((j for j in range(i+1,len(lines)) if re.match(r'^[0-9a-f]+ <',lines[j])),min(len(lines),i+500));keep.update(range(i,end))
print('\n'.join(lines[i] for i in sorted(keep)))
p=b/'frameworks/native/include/input/PropertyMap.h';print('SDK37_HEADER',hashlib.sha256(p.read_bytes()).hexdigest());print(p.read_text())
for rel in ['device/amazon/karnak/libshims/libui/GraphicBuffer.cpp','frameworks/native/libs/ui/Android.bp']:
 p=b/rel;print('SOURCE',rel,p.exists())
 if p.exists():print('SHA256',hashlib.sha256(p.read_bytes()).hexdigest());print(p.read_text())
