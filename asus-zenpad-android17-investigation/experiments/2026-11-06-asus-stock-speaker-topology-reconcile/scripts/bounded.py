"""Sequential host subprocess runner: finite timeout, CPU budget, and resource receipt."""
import json, os, platform, resource, subprocess, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
LOG=ROOT/'evidence/commands.jsonl'
def run(argv, *, cwd=None, env=None, timeout=45, output=None):
    def limits():
        resource.setrlimit(resource.RLIMIT_CPU,(30,30))
        resource.setrlimit(resource.RLIMIT_FSIZE,(128*1024*1024,128*1024*1024))
        resource.setrlimit(resource.RLIMIT_CORE,(0,0))
        try: resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
        except (ValueError,OSError): pass
    start=time.monotonic()
    p=subprocess.run(list(map(str,argv)),cwd=cwd or ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout,preexec_fn=limits)
    if output: (ROOT/output).write_bytes(p.stdout)
    row={'argv':list(map(str,argv)),'cwd':str(cwd or ROOT),'exit':p.returncode,'seconds':round(time.monotonic()-start,3),'timeout_s':timeout,'cpu_s':30,'requested_address_space_bytes':1024**3,'output':output,'platform':platform.platform(),'children_peak_rss_bytes_cumulative':resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,'cpu_affinity':'Darwin has no sched_setaffinity; serial processes; compiler threads=1 where supported; no hard CPU-core binding claim'}
    with LOG.open('a') as f: f.write(json.dumps(row)+'\n')
    if p.returncode: raise RuntimeError(p.stdout.decode(errors='replace')[-4000:])
    return p.stdout
