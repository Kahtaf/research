from pathlib import Path
import hashlib,json,subprocess,re,base64
r=Path('/srv/android/asus-camera-property-map-20261106');llvm=Path('/srv/android/lineage24/prebuilts/clang/host/linux-x86/clang-r584948b/bin')
f=Path('/srv/android/asus-camera-arm32-route/cpp-out/sdk37')
header={}
for rel in ['system/core/libutils/include/utils/'+x+'.h' for x in ['String8','VectorImpl','SortedVector','KeyedVector','TypeHelpers','Vector','Errors','Unicode','AllocatorTracker','Compat']]+['prebuilts/clang/host/linux-x86/clang-r584948b/android_libc++/platform/arm/include/c++/v1/__config_site']:
 p=f/rel
 if p.is_file():header[rel]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'data':base64.b64encode(p.read_bytes()).decode()}
result={'headers':header,'providers':{},'traces':{}}
for arch,name in [('arm','asus-camera-arm32-route'),('arm64','asus-camera-source-abi-route')]:
 b=Path('/srv/android')/name; libs=b/'sdk37-libs'; providers={}
 for p in sorted(libs.glob('*.so')):
  data=p.read_bytes(); elf=subprocess.run([str(llvm/'llvm-readelf'),'-h','-d','--dyn-syms','-W',str(p)],capture_output=True,text=True,check=True,timeout=15).stdout
  providers[p.name]={'path':str(p),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'elf':elf}
 result['providers'][arch]=providers
 p=libs/'libutils.so'
 dis=subprocess.run([str(llvm/'llvm-objdump'),'-d','--demangle',*(['--triple=thumbv7-linux-android'] if arch=='arm' else []),str(p)],capture_output=True,text=True,check=True,timeout=20).stdout
 result['traces'][arch]={}
 for block in re.split(r'(?=^[0-9a-f]+ <)',dis,flags=re.M):
  title=block.splitlines()[0] if block else ''
  if any(s in title for s in ['VectorImpl::VectorImpl','VectorImpl::~VectorImpl','VectorImpl::finish_vector','VectorImpl::clear','VectorImpl::release_storage','VectorImpl::_grow','VectorImpl::add(','VectorImpl::indexOf','String8::String8(android::String8','String8::String8(char const','String8::~String8','String8::setTo(android::String8','SharedBuffer::alloc','SharedBuffer::release']):result['traces'][arch][title]=block
p=Path('/srv/android/asus-camera-arm32-route/public/lib_libutils.so')
dis=subprocess.run([str(llvm/'llvm-objdump'),'-d','--demangle','--triple=thumbv7-linux-android',str(p)],capture_output=True,text=True,check=True,timeout=20).stdout
result['oem-traces']={}
for block in re.split(r'(?=^[0-9a-f]+ <)',dis,flags=re.M):
 title=block.splitlines()[0] if block else ''
 if any(s in title for s in ['PropertyMap::','VectorImpl::VectorImpl','VectorImpl::~VectorImpl','SortedVector<android::key_value_pair_t<android::String8, android::String8> >']):result['oem-traces'][title]=block
print(json.dumps(result))
