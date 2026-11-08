from pathlib import Path
import json,subprocess,hashlib,shlex,base64,re
r=Path('/srv/android/asus-camera-property-map-20261106');f=Path('/srv/android/asus-camera-arm32-route/cpp-out/sdk37');f64=Path('/srv/android/asus-camera-source-abi-route/sdk37')
llvm=Path('/srv/android/lineage24/prebuilts/clang/host/linux-x86/clang-r584948b/bin');clang=str(llvm/'clang++')
commands=[];pins={}
def pin(p):
 p=Path(p);d=p.read_bytes();pins[str(p)]={'sha256':hashlib.sha256(d).hexdigest(),'bytes':len(d)}
def run(args,cwd=r):
 p=subprocess.run(list(map(str,args)),cwd=cwd,text=True,capture_output=True,timeout=40)
 commands.append({'argv':list(map(str,args)),'cwd':str(cwd),'rc':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
 (r/'commands.json').write_text(json.dumps(commands,indent=2));(r/'input-pins.json').write_text(json.dumps(pins,indent=2))
 if p.returncode: print(p.stderr[:6000]);raise RuntimeError('command failed: '+str(args))
 return p.stdout
print(run([clang,'--version']))
common=['-std=c++20','-O2','-g','-fPIC','-fno-exceptions','-fno-rtti','-fvisibility=hidden','-fvisibility-inlines-hidden','-fno-strict-aliasing','-nostdlibinc','-nostdinc++','-DANDROID','-I'+str(r/'src')]
for p in ['system/core/libutils/include','system/core/libutils/binder/include','system/core/libcutils/include','system/logging/liblog/include_vndk','prebuilts/clang/host/linux-x86/clang-r584948b/android_libc++/platform/arm/include/c++/v1','prebuilts/clang/host/linux-x86/clang-r584948b/include/c++/v1']:
 common+=['-I'+str(f/p)]
for arch,target,old,base in [('arm','armv7a-linux-androideabi37','asus-camera-arm32-route',f),('arm64','aarch64-linux-android37','asus-camera-source-abi-route',f64)]:
 out=r/arch;out.mkdir(exist_ok=True)
 flags=common+['-target',target]
 for p in ['bionic/libc/include','bionic/libc/kernel/uapi/asm-'+('arm' if arch=='arm' else 'arm64'),'bionic/libc/kernel/uapi','bionic/libc/kernel/android/scsi','bionic/libc/kernel/android/uapi']:
  flags+=['-isystem',str((base if '/asm-' in p else f)/p)]
 if arch=='arm64':flags+=['-isystem',str(f64/'bionic/libc/kernel/uapi'),'-isystem',str(r/'supplement/libc/kernel/uapi/asm-arm64'),'-isystem',str(r/'supplement/libc/kernel/uapi')]
 if arch=='arm':flags+=['-march=armv8-a','-mcpu=cortex-a53','-mfloat-abi=softfp']
 src=r/'src/legacy_property_map.cpp';obj=out/'legacy_property_map.o'
 deps=run([clang,*flags,'-M',src])
 for n in shlex.split(deps.replace('\\\n',' ').split(':',1)[1]):pin(n)
 layout=run([clang,*flags,'-Xclang','-fdump-record-layouts','-Xclang','-fdump-vtable-layouts','-c',src,'-o',obj])
 (out/'layouts.txt').write_text(layout)
 lib=Path('/srv/android')/old/'sdk37-libs';abi=Path('/srv/android')/old/'abi-out'
 for name in ['libutils.so','liblog.so','libc++.so','libc.so','libm.so','libdl.so']:pin(lib/name)
 for name in ['crtbegin_so.o','crtend_so.o']:pin(abi/name)
 pin(r/'src/exports.map')
 so=out/'libasus_camera_legacy_property_map.so'
 run([clang,'-target',target,'-fuse-ld=lld','-nostdlib','-shared','-Wl,--no-undefined','-Wl,-Bsymbolic','-Wl,--version-script='+str(r/'src/exports.map'),'-Wl,-soname,libasus_camera_legacy_property_map.so',abi/'crtbegin_so.o',obj,'-L'+str(lib),'-lutils','-llog','-lc++','-lc','-lm','-ldl',abi/'crtend_so.o','-o',so])
 (out/'elf.txt').write_text(run([llvm/'llvm-readelf','-h','-d','--dyn-syms','-W',so]))
 (out/'disassembly.txt').write_text(run([llvm/'llvm-objdump','-d','--demangle',so]))
 # Behavior program also compiled for both real target widths; never executed here.
 run([clang,*flags,'-c',r/'tests/behavior.cpp','-o',out/'behavior.o'])
print('PASS both target widths: compiled adapter and behavior test, linked adapter --no-undefined; no target execution')
print('COMMANDS',len(commands),'INPUTS',len(pins))
