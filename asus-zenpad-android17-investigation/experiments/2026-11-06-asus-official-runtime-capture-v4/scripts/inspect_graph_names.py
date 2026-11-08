import json,os,resource,sqlite3,time
from pathlib import Path
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(120,120))
r=Path('/srv/android/asus-official-runtime-capture/preparation-v4');start=time.monotonic()
db=sqlite3.connect('file:'+str(r/'graph-qualification-002/graph-index.sqlite')+'?mode=ro&immutable=1',uri=True)
rows=[]
for pattern in ('%system-build.prop%build.prop%','%com.android.runtime%com.android.runtime.apex'):
 rows += [{'kind':x[0],'name':x[1],'file':x[2],'line':x[3],'raw_prefix':x[4]} for x in db.execute('SELECT kind,name,file,line,substr(text,1,1800) FROM blocks WHERE name LIKE ? LIMIT 8',(pattern,))]
directives=[]
for name in ('out/build-lineage_p00a.ninja','out/soong/build.lineage_p00a.ninja','out/combined-lineage_p00a.ninja'):
 with (r/'graph-fixture/frozen'/name).open('rb') as f:
  for i,line in enumerate(iter(lambda:f.readline(32*1024**2+1),b''),1):
   if line.startswith((b'subninja ',b'include ')):
    if len(directives)>=128:raise RuntimeError('directive count')
    directives.append({'file':name,'line':i,'text':line[:4096].decode()})
u=resource.getrusage(resource.RUSAGE_SELF)
result={'matches':rows,'directives':directives,'elapsed_seconds':round(time.monotonic()-start,3),'cpu_seconds':round(u.ru_utime+u.ru_stime,3),'max_rss_KiB':u.ru_maxrss,'cpu_count':1,'address_space_limit_bytes':1024**3}
with (r/'graph-qualification-002/name-inspection.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(result,indent=2))
