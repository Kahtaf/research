from pathlib import Path
import subprocess as s,shutil,json,hashlib,os
R=Path('/srv/android/asus-firstboot-runtime');P=Path('/srv/android/asus-android17-runtime-prereqs');T=Path('/srv/android/lineage24');I=R/'inputs/observer-r1';assert not I.exists();I.mkdir();os.environ['TMPDIR']=str(R/'tmp')
assert json.loads((R/'evidence/kernel-status.json').read_text())['returncode']==0
shutil.copytree(P/'inputs/headers/bionic',I/'headers/bionic');H=I/'headers'
for n in ['crtbegin_dynamic.o','crtend_android.o']:shutil.copyfile(P/'inputs'/n,I/n)
C=T/'prebuilts/clang/host/linux-x86/clang-r584948b';cmd=[str(C/'bin/clang'),'--target=aarch64-linux-android37','-mno-outline-atomics','-std=gnu11','-O2','-Wall','-Wextra','-Werror','-nostdinc','-nostdlib','-fPIE','-pie','-DANDROID','-Wl,--dynamic-linker=/system/bin/linker64','-MD','-MF',str(I/'observer.d')]
for p in [H/'bionic/libc/include',H/'bionic/libc/kernel/uapi/asm-arm64',H/'bionic/libc/kernel/uapi',H/'bionic/libc/kernel/android/uapi',Path(s.check_output([str(C/'bin/clang'),'-print-resource-dir'],text=True).strip())/'include']:cmd+=['-isystem',str(p)]
libs=R/'inputs/early-r1/root/system/lib64';cmd += [str(I/'crtbegin_dynamic.o'),str(R/'source/observer.c'),'-L'+str(libs),'-Wl,-rpath-link,'+str(libs),'-lc','-lm','-ldl',str(I/'crtend_android.o'),'-o',str(R/'artifacts/observer')]
p=s.run(cmd,capture_output=True,text=True);(R/'evidence/observer-compile.json').write_text(json.dumps(dict(command=cmd,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr),indent=2));assert p.returncode==0,p.stderr
print('observer',hashlib.sha256((R/'artifacts/observer').read_bytes()).hexdigest())
