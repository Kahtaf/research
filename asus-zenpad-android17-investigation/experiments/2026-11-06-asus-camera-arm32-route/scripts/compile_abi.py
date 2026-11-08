from pathlib import Path
import os,resource,subprocess,json,shlex,hashlib,shutil,re
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
b=Path('/srv/android/lineage24');r=Path('/srv/android/asus-camera-arm32-route');out=r/'abi-out';out.mkdir(exist_ok=True)
source=r/'camera_abi_probe.c'
old=json.loads(Path('/srv/android/asus-minimal-audio-hal-20261106/out/compile.json').read_text())[0]['argv'];clang=old[0];flags=old[1:old.index('-MD')]
flags=[f for f in flags if not f.startswith('-I/srv/android/asus-minimal-audio')]
flags=[f.replace('asm-arm64','asm-arm').replace('/platform/aarch64/','/platform/arm/') for f in flags]
flags=[f for f in flags if f != '-target' and not any(x in f for x in ['aarch64', 'armv8', 'mbranch-protection', 'ffixed-x18', 'mno-outline-atomics', 'fstack-clash-protection'])]
flags += ['-target','armv7a-linux-androideabi37','-march=armv8-a','-mcpu=cortex-a53','-mfloat-abi=softfp']
flags+=['-Isystem/media/camera/include','-Isystem/media/graphics/include']
receipts=[]
def run(argv,cwd=b):
 p=subprocess.run(list(map(str,argv)),cwd=cwd,capture_output=True,text=True,timeout=45)
 receipts.append({'argv':list(map(str,argv)),'cwd':str(cwd),'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
 (out/'compile.json').write_text(json.dumps(receipts,indent=2)+'\n')
 print('RC',p.returncode,'STDERR',p.stderr[:4000])
 if p.returncode:raise SystemExit(p.returncode)
 return p.stdout
# Dependency scan only, then freeze every transitive header before compilation.
deps=run([clang,*flags,'-M',source])
paths=shlex.split(deps.replace('\\\n',' ').split(':',1)[1]);pins=[]
for name in paths:
 p=Path(name);p=p if p.is_absolute() else b/p
 if p==source:continue
 try:rel=p.relative_to(b)
 except ValueError:raise RuntimeError('Unexpected dependency '+str(p))
 data=p.read_bytes();assert len(data)<3*1024**2
 dest=r/'sdk37'/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
 pins.append({'source':str(p),'frozen':str(dest),'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)})
# -I/-isystem are relative to frozen root; toolchain resource includes redirected.
flags += ['-resource-dir',str(r/'sdk37/prebuilts/clang/host/linux-x86/clang-r584948b/lib/clang/21')]
# Actual clang resource version is discovered, not assumed.
resource_dir=run([clang,'-print-resource-dir']).strip()
flags[-1]=str(r/'sdk37'/Path(resource_dir).relative_to(b))
run([clang,*flags,'-c',source,'-o',out/'camera_abi_probe.o'],cwd=r/'sdk37')
libdir=r/'sdk37-libs'
for rel in ['bionic/libc/crtbegin_so/android_vendor_arm_armv8-a_cortex-a53/crtbegin_so.o','bionic/libc/crtend_so/android_vendor_arm_armv8-a_cortex-a53/crtend_so.o']:
 p=b/'out/soong/.intermediates'/rel;data=p.read_bytes();dest=out/p.name;dest.write_bytes(data);pins.append({'source':str(p),'frozen':str(dest),'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)})
meta=b/'out/soong/.intermediates/system/media/camera/libcamera_metadata/android_arm_armv8-a_cortex-a53_shared/libcamera_metadata.so'
if not (libdir/'libcamera_metadata.so').exists():(libdir/'libcamera_metadata.so').write_bytes(meta.read_bytes())
for name in ['libcamera_metadata.so','libc.so']:
 p=libdir/name;pins.append({'frozen':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size})
run([clang,'-target','armv7a-linux-androideabi37','-nostdlib','-shared','-fuse-ld=lld','-Wl,--no-undefined','-Wl,-soname,libp00a_camera_abi_probe.so',out/'crtbegin_so.o',out/'camera_abi_probe.o','-L'+str(libdir),'-lcamera_metadata','-lc',out/'crtend_so.o','-o',out/'libp00a_camera_abi_probe.so'])
readelf=Path(clang).parent/'llvm-readelf'
print(run([readelf,'-h','-d','--dyn-syms','-x','.rodata',out/'libp00a_camera_abi_probe.so']))
(out/'input-pins.json').write_text(json.dumps(pins,indent=2)+'\n')
print('INPUT_PINS',json.dumps(pins));print('COMMAND_RECEIPTS',json.dumps(receipts))
print('PASS ABI witness compile/link only; no target execution; no camera implementation')
