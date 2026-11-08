from pathlib import Path
import subprocess as s,json,hashlib
R=Path('/srv/android/asus-android17-runtime-prereqs');I=R/'inputs';H=I/'headers';T=Path('/srv/android/lineage24'); C=T/'prebuilts/clang/host/linux-x86/clang-r584948b'
# Compiler and its bundled resource/C++ headers are immutable prebuilt toolchain inputs.
cmd=[str(C/'bin/clang++'),'--target=aarch64-linux-android37','-mno-outline-atomics','-std=gnu++20','-O2','-Wall','-Werror','-nostdinc','-nostdlib','-fPIE','-pie','-fno-exceptions','-fno-rtti','-DANDROID','-Wl,--dynamic-linker=/system/bin/linker64']
for p in [H/'frameworks/native/libs/binder/include',H/'system/core/libutils/include',H/'system/core/libcutils/include',H/'system/core/libsystem/include',H/'system/logging/liblog/include',H/'system/libbase/include',C/'include/c++/v1',H/'bionic/libc/include',H/'bionic/libc/kernel/uapi/asm-arm64',H/'bionic/libc/kernel/uapi',H/'bionic/libc/kernel/android/uapi',Path(s.check_output([str(C/'bin/clang'),'-print-resource-dir'],text=True).strip())/'include']:
 cmd+=['-isystem',str(p)]
cmd += [str(I/'crtbegin_dynamic.o'),str(R/'source/binder_probe.cpp'),'-L'+str(I/'root/system/lib64'),'-Wl,-rpath-link,'+str(I/'root/system/lib64'),'-lbinder','-llog','-lutils','-lc++','-lc','-lm','-ldl',str(I/'crtend_android.o'),'-o',str(R/'artifacts/binder-probe')]
(R/'evidence/binder-compile-command-r5.json').write_text(json.dumps(cmd,indent=2)+'\n')
p=s.run(cmd,stdout=s.PIPE,stderr=s.STDOUT,text=True);(R/'evidence/binder-compile-r5.txt').write_text(p.stdout+f'\nexit={p.returncode}\n'); print(p.stdout);raise SystemExit(p.returncode)
