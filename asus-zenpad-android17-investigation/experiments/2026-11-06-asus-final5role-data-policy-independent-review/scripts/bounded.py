"""Serial local host commands; retain every result, including failed attempts."""
from pathlib import Path
import json,os,resource,signal,subprocess,time,fcntl,datetime
R=Path(__file__).resolve().parents[1]
LOG=R/'evidence/commands.jsonl'
CEILING=1024**3
STARTED=time.monotonic()

def limits():
    resource.setrlimit(resource.RLIMIT_CPU,(60,60))
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))

def run(args,expect=0,timeout=120,cwd=None):
    with (R/"tmp/host-command.lock").open("a") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        assert time.monotonic()-STARTED<300,"suite command-start deadline"
        return _run(args,expect,timeout,cwd)

def _run(args,expect=0,timeout=120,cwd=None):
    args=list(map(str,args));started=time.monotonic();started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()
    env=dict(os.environ,TMPDIR=str(R/'tmp'),LC_ALL='C',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MAKEFLAGS='-j1')
    p=subprocess.Popen(args,cwd=cwd or R,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,start_new_session=True,preexec_fn=limits)
    try: out,err=p.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        os.killpg(p.pid,signal.SIGKILL);out,err=p.communicate();err+='\nWALL_TIMEOUT'
    rss=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    row=dict(started_utc=started_utc,serialized_host_command=True,argv=args,returncode=p.returncode,stdout=out,stderr=err,elapsed_seconds=time.monotonic()-started,observed_children_maxrss_bytes=rss,wall_timeout_seconds=timeout,cpu_limit_seconds_per_process=60)
    with LOG.open('a') as f:f.write(json.dumps(row)+'\n')
    assert rss<CEILING,row
    if expect is not None:assert p.returncode==expect,row
    return subprocess.CompletedProcess(args,p.returncode,out,err)

if __name__=='__main__':
    attempts=[]
    for name in ['RLIMIT_AS','RLIMIT_DATA','RLIMIT_RSS']:
        code='import resource; r=resource.'+name+'; resource.setrlimit(r,('+str(CEILING)+','+str(CEILING)+')); print(resource.getrlimit(r))'
        p=run(['python3','-B','-c',code],expect=None,timeout=10)
        attempts.append(dict(limit=name,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr))
    (R/'evidence/resource-limit-probes.json').write_text(json.dumps(dict(platform=os.uname().sysname,memory_probes=attempts,serial=True,make_jobs=1,affinity_available=hasattr(os,'sched_setaffinity'),hard_affinity_or_memory_quota_claimed=False,observed_memory_acceptance_bytes=CEILING),indent=2)+'\n')
