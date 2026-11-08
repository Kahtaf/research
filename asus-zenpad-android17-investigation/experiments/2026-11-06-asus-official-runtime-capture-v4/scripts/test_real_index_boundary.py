"""Expected real-scale 3-GiB index refusal; preserve the failed index."""
import datetime,json,os,resource,sys,time
from pathlib import Path
ROOT=Path('/srv/android/asus-official-runtime-capture/preparation-v4')
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(180,180));resource.setrlimit(resource.RLIMIT_FSIZE,(3*1024**3,3*1024**3))
sys.path.insert(0,str(ROOT/'source'))
from graph import Graph
from safeio import Tree,Refusal,need,write_json
fixture=ROOT/'graph-boundary-3g';fixture.mkdir(mode=0o700)
limits=json.loads((ROOT/'inputs/profile-r8.json').read_bytes())['limits'];limits['index_bytes']=3*1024**3
full=json.loads((ROOT/'graph-qualification-003/qualification.json').read_bytes())
need(full['index_bytes']>limits['index_bytes'],'BOUNDARY','full measured index must exceed old ceiling')
tree=Tree(ROOT/'graph-qualification-003/frozen')
for path,pin in full['frozen'].items():need(pin==tree.digest(path,limits['graph_file_bytes']),'DRIFT',path)
start=time.monotonic();code=None;error=None
try:
 graph=Graph(tree,list(full['frozen']),fixture/'graph-index.sqlite',limits);graph.close()
except Refusal as failure:code=failure.code;error=str(failure)
finally:tree.close()
u=resource.getrusage(resource.RUSAGE_SELF);size=(fixture/'graph-index.sqlite').stat().st_size
r={'schema':1,'scope':'owned-frozen-graphs-only','expected_refusal':'INDEX_SIZE','actual_refusal':code,'error':error,'pass':code=='INDEX_SIZE' and size<=3*1024**3,'index_hard_ceiling_bytes':3*1024**3,'failed_index_preserved_bytes':size,'elapsed_index_seconds':round(time.monotonic()-start,3),'cpu_seconds':round(u.ru_utime+u.ru_stime,3),'cpu_seconds_limit':180,'wall_seconds_limit':240,'max_rss_KiB':u.ru_maxrss,'cpu_count':len(os.sched_getaffinity(0)),'address_space_limit_bytes':1024**3,'no_actual_capture':True}
write_json(fixture/'boundary.json',r);print(json.dumps(r,indent=2));raise SystemExit(0 if r['pass'] else 1)
