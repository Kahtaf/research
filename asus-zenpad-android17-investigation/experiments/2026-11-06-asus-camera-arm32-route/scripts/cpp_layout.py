from pathlib import Path
import os,resource,subprocess,json,shlex,hashlib
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
r=Path('/srv/android/asus-camera-arm32-route');b=Path('/srv/android/lineage24');out=r/'cpp-out';out.mkdir(exist_ok=True)
source=out/'layout.cpp';source.write_text('#include <ui/GraphicBuffer.h>\n#include <input/PropertyMap.h>\nextern "C" const unsigned p00a_cpp_sizes[] = {sizeof(android::GraphicBuffer),sizeof(ANativeWindowBuffer),sizeof(android::RefBase),sizeof(android::PropertyMap)};\n')
old=json.loads((r/'abi-out/compile.json').read_text())[0]['argv'];clang=old[0];flags=old[1:old.index('-M')]
flags=[x for x in flags if not x.startswith('-std=') and not any(s in x for s in ['__ANDROID_VNDK__','__ANDROID_VENDOR__'])]
flags+=['-std=c++20','-Wno-error','-Wno-invalid-offsetof']
incs=['external/fmtlib/include','out/soong/.intermediates/hardware/interfaces/graphics/common/aidl/android.hardware.graphics.common-V7-ndk-source/gen/include','frameworks/native/libs/ui/include','frameworks/native/libs/nativewindow/include','frameworks/native/libs/nativebase/include','frameworks/native/libs/arect/include','frameworks/native/libs/math/include','frameworks/native/libs/gui/include','frameworks/native/libs/input','frameworks/native/include','system/core/libutils/include','system/core/libutils/binder/include','system/core/libcutils/include','system/core/libsystem/include','system/libbase/include','system/logging/liblog/include','system/core/libsystem/include','system/core/libprocessgroup/include','system/core/libvndksupport/include','system/media/graphics/include','system/core/libsync/include','frameworks/native/libs/binder/include','frameworks/native/libs/binder/ndk/include_cpp','frameworks/native/libs/binder/ndk/include_ndk']
for base in ['hardware/interfaces/graphics/common/1.0','hardware/interfaces/graphics/common/1.1','hardware/interfaces/graphics/common/1.2','system/libhidl/transport/base/1.0']:
 for p in (b/'out/soong/.intermediates'/base).glob('*/gen'):
  incs.append(str(p.relative_to(b)))
incs += ['system/libhidl/base/include','system/libhidl/transport/include','system/libhwbinder/include','system/libfmq/include','system/libfmq/base']
flags+=['-I'+x for x in incs]
receipts=[]
def run(a,cwd):
 p=subprocess.run(a,cwd=cwd,text=True,capture_output=True,timeout=45);receipts.append({'argv':a,'cwd':str(cwd),'rc':p.returncode,'stdout':p.stdout,'stderr':p.stderr});(out/'commands.json').write_text(json.dumps(receipts,indent=2));return p
p=run([clang,*flags,'-M',str(source)],b)
if p.returncode: print(p.stderr);raise SystemExit(1)
pins=[]
for n in shlex.split(p.stdout.replace('\\\n',' ').split(':',1)[1]):
 q=Path(n);q=q if q.is_absolute() else b/q
 if q==source:continue
 rel=q.relative_to(b);d=q.read_bytes();dst=out/'sdk37'/rel;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(d);pins.append({'source':str(q),'sha256':hashlib.sha256(d).hexdigest(),'bytes':len(d)})
res=subprocess.run([clang,'-print-resource-dir'],text=True,capture_output=True,check=True).stdout.strip();flags+=['-resource-dir',str(out/'sdk37'/Path(res).relative_to(b))]
p=run([clang,*flags,'-Xclang','-fdump-record-layouts','-c',str(source),'-o',str(out/'layout.o')],out/'sdk37')
print(p.stderr)
if p.returncode:raise SystemExit(1)
blocks=p.stdout.split('*** Dumping AST Record Layout');print('\n'.join(x for x in blocks if any(s in x for s in ['class android::GraphicBuffer\n','class android::PropertyMap\n','struct ANativeWindowBuffer\n'])))
print(subprocess.run([str(Path(clang).parent/'llvm-readelf'),'-x','.rodata',str(out/'layout.o')],text=True,capture_output=True).stdout)
(out/'pins.json').write_text(json.dumps(pins,indent=2));print('PASS',len(pins),'frozen headers')
