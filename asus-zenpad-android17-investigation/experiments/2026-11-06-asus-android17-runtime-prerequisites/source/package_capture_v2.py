from pathlib import Path
import hashlib,json,shutil,tarfile
R=Path('/srv/android/asus-android17-runtime-prereqs');C=R/'compact-r2';assert not C.exists();C.mkdir()
shutil.copytree(R/'evidence',C/'evidence');shutil.copytree(R/'source',C/'source',ignore=shutil.ignore_patterns('__pycache__'))
for run in sorted(R.glob('run-r*')):
 dest=C/'evidence'/run.name;dest.mkdir()
 for p in run.iterdir():
  if p.suffix in ['.json','.log','.txt','.c','.cpp','.py','.h','.exit']:shutil.copyfile(p,dest/p.name)
art=C/'artifacts';art.mkdir()
shutil.copyfile(R/'build-r4/.config',art/'kernel-runtime-r4.config')
manifest=[{'path':str(p.relative_to(C)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(C.rglob('*')) if p.is_file()]
(art/'capture-manifest-r2.json').write_text(json.dumps(manifest,indent=2)+'\n')
archive=R/'artifacts/compact-r2.tar.gz'
with tarfile.open(archive,'w:gz') as t:
 for p in sorted(C.rglob('*')):
  if p.is_file():t.add(p,arcname=str(p.relative_to(C)))
print(json.dumps({'path':str(archive),'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'bytes':archive.stat().st_size,'files':len(manifest)},indent=2))
