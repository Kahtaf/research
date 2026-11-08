import json, os, platform, resource, signal, subprocess, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def limits():
    resource.setrlimit(resource.RLIMIT_CPU,(30,30))
    resource.setrlimit(resource.RLIMIT_FSIZE,(64*1024**2,64*1024**2))
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    for name in ('RLIMIT_AS','RLIMIT_DATA','RLIMIT_RSS'):
        try: resource.setrlimit(getattr(resource,name),(1024**3,1024**3))
        except (ValueError,OSError): pass
    if hasattr(os,'sched_setaffinity'): os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})

def run(argv,label,expected=0):
    dest=ROOT/'evidence'/label
    start=time.monotonic()
    with dest.open('wb') as f:
        p=subprocess.Popen([str(a) for a in argv],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,preexec_fn=limits,start_new_session=True)
        timed_out=False
        try: code=p.wait(timeout=45)
        except subprocess.TimeoutExpired:
            timed_out=True; os.killpg(p.pid,signal.SIGKILL); code=p.wait()
    row={'argv':[str(a) for a in argv],'exit':code,'timeout':timed_out,'wall_seconds':round(time.monotonic()-start,3),'cpu_limit_seconds':30,'wall_limit_seconds':45,'requested_memory_bytes':1024**3,'cumulative_child_maxrss':resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,'platform':platform.platform(),'reaped':True,'log':label}
    with (ROOT/'evidence/commands.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
    assert not timed_out and code==expected,(row,dest.read_text(errors='replace')[-3000:])
    print(label,code)
    return dest.read_text(errors='replace')

if __name__=='__main__':
    observations={}
    for name in ('RLIMIT_AS','RLIMIT_DATA','RLIMIT_RSS'):
        try: resource.setrlimit(getattr(resource,name),(1024**3,1024**3));observations[name]='accepted; not proof of enforcement'
        except (ValueError,OSError) as e: observations[name]=repr(e)
    observations['affinity']='available' if hasattr(os,'sched_setaffinity') else 'Darwin: no sched_setaffinity; hard one-CPU cap unavailable'
    (ROOT/'evidence/limits.json').write_text(json.dumps(observations,indent=2)+'\n')
    print(json.dumps(observations))
