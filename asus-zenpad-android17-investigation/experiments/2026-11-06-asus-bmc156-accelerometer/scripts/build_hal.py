from pathlib import Path
import subprocess as s,json,os,hashlib,resource
R=Path('/srv/android/asus-bmc156-accelerometer-r1');A=Path('/srv/android/lineage24');H=R/'sdk/headers';O=R/'hal-out';O.mkdir(exist_ok=True)
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});os.environ['TMPDIR']=str(R/'tmp')
C=A/'prebuilts/clang/host/linux-x86/clang-r596125/bin/clang';resource_dir=Path(s.check_output([str(C),'-print-resource-dir'],text=True).strip())
includes=[H/'hardware/libhardware/include_all',H/'system/core/libcutils/include',H/'system/core/libsystem/include',H/'bionic/libc/include',H/'bionic/libc/kernel/uapi/asm-arm64',H/'bionic/libc/kernel/uapi',H/'bionic/libc/kernel/android/uapi',resource_dir/'include']
flags=[str(C),'--target=aarch64-linux-android37','-mno-outline-atomics','-std=gnu11','-O2','-fPIC','-Wall','-Wextra','-Werror','-nostdinc','-DANDROID']
for p in includes:flags+=['-isystem',str(p)]
results=[]
def run(cmd,name):
 p=s.run(cmd,capture_output=True,text=True);r=dict(command=cmd,exit=p.returncode,stdout=p.stdout,stderr=p.stderr);results.append(r);(R/'evidence/hal-build.json').write_text(json.dumps(results,indent=2)+'\n');print(name,p.returncode,p.stdout,p.stderr,flush=True);assert p.returncode==0
for name in ['accel_protocol','sensors']:
 src=R/'source/hal'/(name+'.c');obj=O/(name+'.o')
 run(flags+['-MD','-MF',str(O/(name+'.d')),'-c',str(src),'-o',str(obj)],name)
run([str(C),'--target=aarch64-linux-android37','-fuse-ld=lld','-nostdlib','-shared','-Wl,--no-undefined,-soname,sensors.mt8163.so',str(R/'sdk/lib/crtbegin_so.o'),str(O/'sensors.o'),str(O/'accel_protocol.o'),'-L'+str(R/'sdk/lib'),'-lc',str(R/'sdk/lib/crtend_so.o'),'-o',str(O/'sensors.mt8163.so')],'link')
run(['readelf','-h','-d','-Ws',str(O/'sensors.mt8163.so')],'ELF')
run(['gcc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-fsanitize=undefined,bounds','-I'+str(R/'source/hal'),str(R/'source/hal/accel_protocol.c'),str(R/'source/tests/test_protocol.c'),'-o',str(O/'test_protocol')],'host boundary compile')
def limits():resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(30,30))
p=s.run([str(O/'test_protocol')],capture_output=True,text=True,preexec_fn=limits,timeout=35);print(p.stdout,p.stderr);(R/'evidence/protocol-test.json').write_text(json.dumps(dict(exit=p.returncode,stdout=p.stdout,stderr=p.stderr,one_cpu=True,address_space_bytes=1024**3),indent=2)+'\n');assert p.returncode==0
