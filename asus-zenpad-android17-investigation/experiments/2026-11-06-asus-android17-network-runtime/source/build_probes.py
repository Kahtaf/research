from pathlib import Path
import os
os.makedirs("/srv/android/asus-network-runtime/tmp",exist_ok=True)
os.environ["TMPDIR"]="/srv/android/asus-network-runtime/tmp"
import subprocess as s,json,sys
R=Path('/srv/android/asus-network-runtime');I=R/'inputs';H=I/'headers';C=Path('/srv/android/lineage24/prebuilts/clang/host/linux-x86/clang-r584948b');Conn=R/'staged-network' if os.environ.get('NETWORK_STAGED') else I/'Connectivity'; E=I/'extra'
base=[str(C/'bin/clang++'),'--target=aarch64-linux-android31','-mno-outline-atomics','-std=gnu++20','-O2','-nostdinc','-nostdlib','-fPIE','-pie','-fno-exceptions','-fno-rtti','-ffunction-sections','-fdata-sections','-Wl,--gc-sections','-DFMT_HEADER_ONLY','-DANDROID','-D__ANDROID_APEX__','-Wl,--dynamic-linker=/system/bin/linker64']
incs=[I/'netd-include/mainline',E/'external/fmtlib/include',I,Conn/'bpf/headers/include',Conn/'bpf/progs',Conn/'staticlibs/native/bpf_headers/include',Conn/'bpf/syscall_wrappers/include',Conn/'bpf/progs/include',E/'external/libbpf/src',E/'external/libbpf/android',E/'system/core/libcutils/include',H/'system/core/libutils/include',H/'system/logging/liblog/include',H/'system/libbase/include',C/'include/c++/v1',H/'bionic/libc/include',H/'bionic/libc/kernel/uapi/asm-arm64',H/'bionic/libc/kernel/uapi',H/'bionic/libc/kernel/android/uapi',Path(s.check_output([str(C/'bin/clang'),'-print-resource-dir'],text=True).strip())/'include']
# libbpf installed header layout, preserving source contents.
(I/'bpf').mkdir(exist_ok=True)
for p in (E/'external/libbpf/src').glob('*.h'):(I/'bpf'/p.name).write_bytes(p.read_bytes())
for p in incs:base+=['-isystem',str(p)]
for name in ['seed_properties','loader_probe','handler_probe','policy_probe','network_probe','network_loader','loader_negative','cross_profile_probe']:
 if os.environ.get('NETWORK_ONLY') and name not in os.environ['NETWORK_ONLY'].split(','):continue
 cmd=base+(['-DNETWORK_STAGED'] if os.environ.get('NETWORK_STAGED') else [])+[str(I/'crtbegin_dynamic.o'),str(R/'source'/(name+'.cpp')),'-L'+str(I/'root/system/lib64'),'-Wl,-rpath-link,'+str(I/'root/system/lib64'),'-lbase','-llog','-lbpf','-lc++','-lc','-lm','-ldl',str(C/'lib/clang/22/lib/linux/libclang_rt.builtins-aarch64-android.a'),str(I/'crtend_android.o'),'-o',str(R/'artifacts'/name)]
 cmd+=['-MD','-MF',str(R/'artifacts'/(name+'.d'))]
 p=s.run(cmd,capture_output=True,text=True);(R/'evidence'/(name+'-compile-'+sys.argv[1]+'.log')).write_text(json.dumps(cmd)+'\n'+p.stdout+p.stderr);print(name,p.returncode,p.stderr);assert p.returncode==0

# Each successful artifact has a transitive input hash manifest.
import shlex,hashlib
for dep in (R/'artifacts').glob('*.d'):
 if dep.stem not in ['seed_properties','loader_probe','handler_probe','policy_probe','network_probe','network_loader','loader_negative','cross_profile_probe']:continue
 text=dep.read_text().replace('\\\n',' ');paths=shlex.split(text.split(':',1)[1]);manifest={}
 for name in paths:
  p=Path(name)
  if p.is_file():manifest[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
 (R/'evidence'/(dep.stem+'-inputs-'+sys.argv[1]+'.json')).write_text(json.dumps(manifest,indent=2)+'\n')
