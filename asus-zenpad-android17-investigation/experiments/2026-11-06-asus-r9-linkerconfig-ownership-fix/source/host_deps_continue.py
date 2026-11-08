from pathlib import Path
import os,json,subprocess as s,tarfile,hashlib,resource
R=Path('/srv/android/asus-r9-linkerconfig-ownership-fix-20261106');D=R/'inputs/host-deps';os.environ['TMPDIR']=str(R/'tmp');os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(4*1024**3,4*1024**3));log=[]
for project,dest in [('system/libbase','libbase'),('external/fmtlib','fmtlib')]:
 git=Path('/srv/android/lineage24')/project/'.git';rev=s.check_output(['git','--git-dir='+str(git),'rev-parse','HEAD'],text=True,timeout=10).strip();arc=D/(dest+'.tar')
 if not arc.exists():
  with arc.open('wb') as f:p=s.run(['git','--git-dir='+str(git),'archive','--format=tar',rev],stdout=f,stderr=s.PIPE,timeout=20);assert p.returncode==0
 with tarfile.open(arc) as tf:
  members=[m for m in tf.getmembers() if m.isfile() or m.isdir()];tf.extractall(D/dest,members=members,filter='data')
 log.append(dict(project=project,git_commit=rev,archive_sha256=hashlib.sha256(arc.read_bytes()).hexdigest(),omitted_symlinks='formatting metadata only; source/header regular files retained'))
for project,path in [('build/soong','linkerconfig/proto/linker_config.proto'),('system/apex','proto/apex_manifest.proto')]:
 git=Path('/srv/android/lineage24')/project/'.git';rev=s.check_output(['git','--git-dir='+str(git),'rev-parse','HEAD'],text=True).strip();b=s.check_output(['git','--git-dir='+str(git),'show',rev+':'+path],timeout=10);(D/Path(path).name).write_bytes(b);log.append(dict(project=project,git_commit=rev,path=path,sha256=hashlib.sha256(b).hexdigest()))
(R/'evidence/host-dependency-acquisition.json').write_text(json.dumps(dict(log=log,deb_pins={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (D/'packages').glob('*.deb')},preserved_preparation_failure='tar data filter refused upstream .clang-format symlink outside isolated source subtree; extraction resumed with regular source/header files only',note='Host source algorithm tests with genuine source dependencies and isolated distro development packages; not an admitted ARM64 leaf closure'),indent=2));print((D/'libbase/Android.bp').read_text()[:12000]);print((D/'linker_config.proto').read_text());print((D/'apex_manifest.proto').read_text()[:7000])
