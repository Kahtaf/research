from pathlib import Path
import os,json,shutil,hashlib,subprocess as s,resource
R=Path('/srv/android/asus-odsign-startup-20261106');P=Path('/srv/android/asus-r9-linkerconfig-ownership-fix-20261106');G=Path('/srv/android/asus-genuine-service-runtime');T=R/'inputs/tools';old=Path('/srv/android/asus-full-system-observer-preparation-20261106/immutable');os.environ['TMPDIR']=str(R/'tmp');os.sched_setaffinity(0,{0});resource.setrlimit(resource.RLIMIT_AS,(4*1024**3,4*1024**3));T.mkdir(exist_ok=True)
for n in ['compiler-bin','toolchain']:shutil.copytree(old/n,T/n,dirs_exist_ok=True)
(T/'bin').mkdir(exist_ok=True);shutil.copyfile(old/'bin/aarch64-linux-gnu-gcc',T/'bin/aarch64-linux-gnu-gcc');os.chmod(T/'bin/aarch64-linux-gnu-gcc',0o755)
tc=T/'toolchain';cmd=[str(T/'bin/aarch64-linux-gnu-gcc'),'-B'+str(T/'compiler-bin')+'/', '-nostdinc','-isystem',str(tc/'gcc-include'),'-isystem',str(tc/'include'),'-static','-nostdlib','-fno-use-linker-plugin','-O2','-Wall','-Wextra','-Werror','-MD','-MF',str(R/'evidence/observer.d'),str(tc/'lib/crt1.o'),str(tc/'lib/crti.o'),str(tc/'gcc/crtbeginT.o'),str(R/'source/observer.c'),'-Wl,--start-group',str(tc/'gcc/libgcc.a'),str(tc/'gcc/libgcc_eh.a'),str(tc/'lib/libc.a'),'-Wl,--end-group',str(tc/'gcc/crtend.o'),str(tc/'lib/crtn.o'),'-o',str(R/'inputs/observer')];p=s.run(cmd,capture_output=True,text=True,timeout=60);(R/'evidence/compile.json').write_text(json.dumps(dict(command=cmd,rc=p.returncode,stdout=p.stdout,stderr=p.stderr),indent=2));assert p.returncode==0,p.stderr
# Adapt retained preparer only in owned prefix. Use precompiled genuine patcher helper; no active compiler/out access.
for n in ['root-enabled-vendor.fstab','root-enabled-vendor.contexts','root-enabled-init.rc'] :shutil.copyfile(P/'inputs'/n,R/'inputs'/n)
shutil.copytree(P/'inputs/runtime-bin-preserved',R/'inputs/runtime-bin-preserved',dirs_exist_ok=True)
shutil.copyfile(P/'inputs/runtime-r3/patcher',R/'inputs/patcher')
src=(P/'source/prepare_runtime_r3_actual.py').read_text().replace(str(P),str(R)).replace('runtime-r3','runtime-r1')
start=src.index('# Narrow retained observer:');end=src.index("(I/'vendor.contexts').write_bytes",start)
src=src[:start]+"shutil.copyfile(R/'inputs/observer',I/'observer')\n"+src[end:]
start=src.index("run(['aarch64-linux-gnu-gcc'");end=src.index('\ndef ent',start)
src=src[:start]+"shutil.copyfile(R/'inputs/patcher',I/'patcher')\n"+src[end:]
src=src.replace("candidate=R/'work/native/arm64-generator.stripped'","candidate=P/'work/native/arm64-generator.stripped'")
# Preserve original shell service and privileges exactly.
(R/'source/prepare_actual.py').write_text(src);exec(compile(src,str(R/'source/prepare_actual.py'),'exec'))
# All dependency and input hashes are public. Never pin or export fresh entropy/DATA.
pins={str(p.relative_to(T)):hashlib.sha256(p.read_bytes()).hexdigest() for p in T.rglob('*') if p.is_file() and not p.is_symlink()};(R/'evidence/compiler-pins.json').write_text(json.dumps(pins,indent=2))
for name in ['execute_runtime_r3.py','verify_runtime_r3_cow.py','audit_runtime_r3_cow.py']:
 f=P/'source'/name
 if not f.exists():continue
 x=f.read_text().replace(str(P),str(R)).replace('runtime-r3','runtime-r1').replace('run-patch-r3','run-patch-r1').replace("+'-r3'","+'-r1'").replace('else 180','else 300').replace('(2*1024+256)*1024**2','1024**3')
 if name.startswith('verify'):x=x.replace("(R/'inputs/runtime-bin-preserved'","(R/'inputs/runtime-bin-preserved'")
 (R/'source'/name.replace('_r3','')).write_text(x)
print('PREPARED_ONE_300S_RUNTIME; static diagnostic compiler entirely owned snapshot; genuine daemon unchanged')
