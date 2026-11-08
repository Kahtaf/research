from pathlib import Path
import subprocess as s,os,json,hashlib,resource,shutil
R=Path('/srv/android/asus-r9-linkerconfig-ownership-fix-20261106');D=R/'inputs/host-deps';os.environ['TMPDIR']=str(R/'tmp');os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(4*1024**3,4*1024**3));E=R/'evidence';W=R/'work/host';W.mkdir();commands=[]
def run(cmd,cwd=None):
 p=s.run(cmd,cwd=cwd,capture_output=True,text=True,timeout=60);commands.append(dict(command=[str(x) for x in cmd],rc=p.returncode,stdout=p.stdout,stderr=p.stderr));(E/'host-build-commands.json').write_text(json.dumps(commands,indent=2));assert p.returncode==0,p.stderr;return p
run(['apt-get','download','libgmock-dev'],cwd=D/'packages')
for p in (D/'packages').glob('libgmock-dev*.deb'):run(['dpkg-deb','-x',str(p),str(D/'root')])
# Public liblog declarations only, captured as immutable Git object source.
git=Path('/srv/android/lineage24/system/logging/.git');rev=s.check_output(['git','--git-dir='+str(git),'rev-parse','HEAD'],text=True).strip();import tarfile
arc=D/'liblog-headers.tar'
with arc.open('wb') as f:p=s.run(['git','--git-dir='+str(git),'archive',rev,'liblog/include'],stdout=f,stderr=s.PIPE,timeout=15);assert p.returncode==0
with tarfile.open(arc) as tf:tf.extractall(D/'logging',members=[m for m in tf.getmembers() if m.isfile() or m.isdir()],filter='data')
# Real protoc + real generated LinkerConfig; no replacement model/header.
env=os.environ.copy();env['LD_LIBRARY_PATH']=str(D/'root/usr/lib/x86_64-linux-gnu');p=s.run([str(D/'root/usr/bin/protoc'),'-I',str(D),'--cpp_out='+str(W),str(D/'linker_config.proto')],env=env,capture_output=True,text=True,timeout=20);assert p.returncode==0,p.stderr
incs=[D/'libbase/include',D/'fmtlib/include',D/'logging/liblog/include',D/'root/usr/include',W]
flags=['-std=gnu++23','-O1','-g0','-DFMT_HEADER_ONLY','-ffunction-sections','-fdata-sections','-pthread']+['-I'+str(p) for p in incs]
# Genuine libbase sources needed by original modules/contents, compiled in isolation.
base=['chrono_utils','file','logging','parsebool','posix_strerror_r','properties','result','stringprintf','strings','threads','errors_unix']
objs=[]
for n in base:
 out=W/('base-'+n+'.o');run(['/usr/bin/g++']+flags+['-c',str(D/'libbase'/(n+'.cpp')),'-o',str(out)]);objs.append(out)
run(['/usr/bin/ar','rcs',str(W/'libbase.a')]+[str(x) for x in objs])
# Use exact original ApexInfo partition methods, excluding the unrelated disk scanner.
src=(R/'inputs/linkerconfig-before/modules/apex.cc').read_text();start=src.index('bool ApexInfo::InSystem() const');end=src.index('}  // namespace modules',start);body=src[start:end];(W/'apex-partition-methods.cc').write_text('#include "linkerconfig/apex.h"\nnamespace android { namespace linkerconfig { namespace modules {\n'+body+'\n}}}\n')
(E/'host-build-profile.json').write_text(json.dumps(dict(compiler='/usr/bin/g++',compiler_sha256=hashlib.sha256(Path('/usr/bin/g++').read_bytes()).hexdigest(),flags=flags,liblog_headers_git_commit=rev,apex_methods_exact_source_sha256=hashlib.sha256(body.encode()).hexdigest(),profile='faithful host compilation of original modules/contents, genuine libbase/protobuf/gtest; not Soong ARM64 target leaf closure',TMPDIR=os.environ['TMPDIR']),indent=2))
print('host dependencies built')
