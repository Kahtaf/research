"""One serial host command at a time, with finite CPU/wall/file bounds."""
import json,os,platform,resource,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def run(args,output,timeout=45,expect=0):
 def limit():
  resource.setrlimit(resource.RLIMIT_CPU,(30,30))
  resource.setrlimit(resource.RLIMIT_FSIZE,(128*1024**2,128*1024**2))
  resource.setrlimit(resource.RLIMIT_CORE,(0,0))
  for name in ['RLIMIT_AS','RLIMIT_DATA','RLIMIT_RSS']:
   try:resource.setrlimit(getattr(resource,name),(1024**3,1024**3))
   except (ValueError,OSError):pass
 t=time.monotonic();p=subprocess.run(list(map(str,args)),cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout,preexec_fn=limit)
 dest=ROOT/output;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(p.stdout)
 row={'argv':list(map(str,args)),'exit':p.returncode,'seconds':round(time.monotonic()-t,3),'timeout_s':timeout,'cpu_s':30,'requested_memory_bytes':1024**3,'children_peak_rss_bytes_cumulative':resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,'output':output,'platform':platform.platform(),'execution':'serial, no workers or parallel builds; Darwin lacks affinity API'}
 with (ROOT/'evidence/commands.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
 assert p.returncode==expect,p.stdout.decode(errors='replace')[-5000:]
 assert row['children_peak_rss_bytes_cumulative']<1024**3
 return p.stdout
