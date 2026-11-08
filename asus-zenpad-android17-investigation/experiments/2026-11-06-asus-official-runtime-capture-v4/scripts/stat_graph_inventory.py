import fnmatch,json,os,resource,stat
from pathlib import Path
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(30,30))
r=Path('/srv/android/asus-official-runtime-capture/preparation-v4');base=Path('/srv/android/lineage24')
selector=json.loads((r/'inputs/selector.json').read_bytes());paths=set();counts={}
for parent,pattern in selector['graphs']:
 count=0
 with os.scandir(base/parent) as entries:
  for e in entries:
   count+=1
   if count>20000:raise RuntimeError('directory entry ceiling')
   if fnmatch.fnmatch(e.name,pattern):
    if not e.is_file(follow_symlinks=False):raise RuntimeError('graph symlink/type')
    paths.add(parent+'/'+e.name)
 counts[parent]=count
# Combined envelope and its package graph are measured separately, not new selectors.
paths.update(('out/combined-lineage_p00a.ninja','out/build-lineage_p00a-package.ninja'))
rows=[]
for path in sorted(paths):
 s=(base/path).lstat()
 if not stat.S_ISREG(s.st_mode):raise RuntimeError('type')
 rows.append({'path':path,'bytes':s.st_size,'selector_match':any(path.startswith(p+'/') and fnmatch.fnmatch(path[len(p)+1:],pattern) for p,pattern in selector['graphs'])})
result={'scope':'generated-graph-names-and-stat-only','graphs':rows,'total_bytes':sum(x['bytes'] for x in rows),'graph_count':len(rows),'directory_entries':counts}
with (r/'graph-fixture/actual-graph-inventory.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(result,indent=2))
