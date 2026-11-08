from pathlib import Path
import os,json,hashlib,subprocess as s,shutil,resource
R=Path('/srv/android/asus-r9-linkerconfig-ownership-fix-20261106');D=Path('/srv/android/asus-device-product');os.environ['TMPDIR']=str(R/'tmp');os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(4*1024**3,4*1024**3))
for n in ['linkerconfig.patch','source-manifest.json']:
 src=D/'revisions/r6'/n;dst=R/'inputs/graphics-r6'/n;dst.parent.mkdir(exist_ok=True,parents=True);shutil.copyfile(src,dst)
pins=json.loads((D/'graphics-result-r7/source-pins.json').read_text());sha=pins['system/linkerconfig'];arc=R/'inputs/linkerconfig-upstream.tar'
p=s.run(['git','--git-dir=/srv/android/lineage24/system/linkerconfig/.git','archive','--format=tar',sha],stdout=arc.open('wb'),stderr=s.PIPE,timeout=30);assert p.returncode==0,p.stderr
# Extract only this public pinned upstream project, never a changing working tree.
import tarfile
with tarfile.open(arc) as tf:
 for m in tf.getmembers():assert not Path(m.name).is_absolute() and '..' not in Path(m.name).parts
 tf.extractall(R/'inputs/linkerconfig-upstream',filter='data')
shutil.copytree(R/'inputs/linkerconfig-upstream',R/'inputs/linkerconfig-before')
commands=[]
for patch in [R/'inputs/compatibility/system-linkerconfig-applied.diff',R/'inputs/graphics-r6/linkerconfig.patch']:
 p=s.run(['patch','-p1','--batch','--forward','-i',str(patch)],cwd=R/'inputs/linkerconfig-before',capture_output=True,text=True,timeout=15);commands.append({'patch':str(patch),'rc':p.returncode,'stdout':p.stdout,'stderr':p.stderr});assert p.returncode==0,p.stdout+p.stderr
manifest=json.loads((D/'revisions/r6/source-manifest.json').read_text());verified={}
for n,row in manifest.items():
 p=R/'inputs/linkerconfig-before'/n;actual=hashlib.sha256(p.read_bytes()).hexdigest();assert actual==row['after_sha256'],(n,actual,row);verified[n]=actual
(R/'evidence/frozen-source.json').write_text(json.dumps(dict(upstream_commit=sha,archive_sha256=hashlib.sha256(arc.read_bytes()).hexdigest(),patches=commands,graphics_r6_postimages_verified=verified),indent=2))
# Only metadata already frozen by prior kit owners; inspect structure and the selected linkerconfig record.
m=json.loads(Path('/srv/android/asus-reviewed-build-kit/r9-exec-r1/inputs/native-lineage-map.json').read_text());hits=[]
def visit(v,path=''):
 if isinstance(v,dict):
  if any(isinstance(x,str) and 'system/linkerconfig/' in x for x in v.values()):hits.append({'json_path':path,'record':v});return
  for k,x in v.items():visit(x,path+'/'+k)
 elif isinstance(v,list):
  for i,x in enumerate(v):visit(x,path+'/'+str(i))
visit(m);(R/'evidence/retained-linkerconfig-lineage.json').write_text(json.dumps(hits,indent=2))
d={'source_verified_files':len(verified),'upstream_commit':sha,'lineage_hit_count':len(hits),'lineage_hits':hits,'available_tools':{}}
for n in ['fsck.erofs','dump.erofs','clang++','g++','cmake','pkg-config']:
 p=s.run(['which',n],capture_output=True,text=True);d['available_tools'][n]=p.stdout.strip()
for p in [Path('/srv/android/asus-device-product/logs'),Path('/srv/android/asus-full-system-observer-preparation-20261106/immutable/bin')]:d[str(p)]=[x.name for x in p.iterdir() if any(y in x.name for y in ['graphics','linker','erofs'])]
print(json.dumps(d,indent=2))
