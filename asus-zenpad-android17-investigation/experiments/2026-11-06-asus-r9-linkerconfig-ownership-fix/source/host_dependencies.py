from pathlib import Path
import os,json,subprocess as s,resource,tarfile,hashlib
R=Path('/srv/android/asus-r9-linkerconfig-ownership-fix-20261106');os.environ['TMPDIR']=str(R/'tmp');os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(4*1024**3,4*1024**3));D=R/'inputs/host-deps';D.mkdir();P=D/'packages';P.mkdir();log=[]
# Host-only faithful source tests; no ARM64 target closure is inferred from these packages.
names=['libgtest-dev','libfmt-dev','libprotobuf-dev','protobuf-compiler','libprotoc32t64','libprotobuf32t64','libprotobuf-lite32t64','erofs-utils']
p=s.run(['apt-cache','show','--no-all-versions']+names,capture_output=True,text=True,timeout=20);(D/'package-metadata.txt').write_text(p.stdout+p.stderr)
existing=[]
for n in names:
 if ('Package: '+n+'\n') in p.stdout:existing.append(n)
p=s.run(['apt-get','download']+existing,cwd=P,capture_output=True,text=True,timeout=90);log.append(dict(command=['apt-get','download']+existing,rc=p.returncode,stdout=p.stdout,stderr=p.stderr));assert p.returncode==0,p.stderr
for deb in sorted(P.glob('*.deb')):
 p=s.run(['dpkg-deb','-x',str(deb),str(D/'root')],capture_output=True,text=True,timeout=20);assert p.returncode==0,p.stderr
# Capture immutable Git objects for the bounded genuine host dependency source projects.
for project,dest in [('system/libbase','libbase'),('external/fmtlib','fmtlib')]:
 git=Path('/srv/android/lineage24')/project/'.git';rev=s.check_output(['git','--git-dir='+str(git),'rev-parse','HEAD'],text=True,timeout=10).strip();arc=D/(dest+'.tar')
 with arc.open('wb') as f:p=s.run(['git','--git-dir='+str(git),'archive','--format=tar',rev],stdout=f,stderr=s.PIPE,timeout=20);assert p.returncode==0
 with tarfile.open(arc) as tf:tf.extractall(D/dest,filter='data')
 log.append(dict(project=project,immutable_git_commit=rev,archive_sha256=hashlib.sha256(arc.read_bytes()).hexdigest()))
# Genuine proto schema belongs to the frozen linkerconfig project already captured.
(R/'evidence/host-dependency-acquisition.json').write_text(json.dumps(dict(log=log,deb_pins={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in P.glob('*.deb')},note='isolated host dependency packages, not a retained ARM64 leaf closure'),indent=2))
print(json.dumps({'packages':[p.name for p in P.glob('*.deb')],'owned_bytes':sum(p.stat().st_size for p in R.rglob('*') if p.is_file()),'dependency_projects':[x for x in log if 'project' in x]},indent=2))
