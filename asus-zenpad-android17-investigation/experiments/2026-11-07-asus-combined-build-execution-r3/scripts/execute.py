"""One authorized ordinary cached build, unlimited AS, eight-hour native deadline."""
from pathlib import Path
import datetime,json,os,resource,subprocess,sys,time,traceback
OWN=Path('/srv/android/asus-combined-build-execution-r3')
KIT=Path('/srv/android/asus-reviewed-build-kit/r9-exec-r1')
sys.path.insert(0,str(KIT/'scripts'))
from integrate import read,write,sha,need,acquire
from lineage import related,stop_owned_handles
plan=read(OWN/'inputs/base-plan.json')
start=time.monotonic(); child=None; phase=None
os.environ.update(PYTHONDONTWRITEBYTECODE='1',GIT_OPTIONAL_LOCKS='0')
lock=acquire(plan)
need(os.fstat(lock.fileno()).st_ino==15018964,'Wrong original lock inode')
need(not (OWN/'attempt').exists(),'Consumed attempt: refuse repeat')
(OWN/'attempt').mkdir();(OWN/'logs').mkdir()
limits=resource.getrlimit(resource.RLIMIT_AS)
write(OWN/'attempt/address-space.json',{'soft':limits[0],'hard':limits[1],'unlimited_value':resource.RLIM_INFINITY,'fresh_ssh':True,'native_or_host_limit_mutation':False})
need(limits==(resource.RLIM_INFINITY,resource.RLIM_INFINITY),'Fresh SSH soft/hard AS not unlimited')
env=dict(os.environ,REVIEWED_BUILD_LOCK_FD=str(lock.fileno()))
def run(argv,filename,name,seconds):
    global child,phase
    phase=name
    with (OWN/'logs'/filename).open('xb') as log:
        child=subprocess.Popen(list(map(str,argv)),stdout=log,stderr=subprocess.STDOUT,env=env,cwd=OWN,pass_fds=(lock.fileno(),))
        stat=(Path('/proc')/str(child.pid)/'stat').read_text().split(') ',1)[1].split()
        write(OWN/'attempt'/(name+'-handle.json'),{'pid':child.pid,'start_ticks':int(stat[19]),'ppid':int(stat[1]),'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'timeout_seconds':seconds,'process_group_actions':False})
        try: code=child.wait(timeout=seconds)
        except subprocess.TimeoutExpired:
            stopped=stop_owned_handles(OWN,child)
            write(OWN/'attempt'/(name+'-timeout.json'),{'exact_owned_handles_signalled':stopped,'shell_returncode':child.returncode,'deadline_seconds':seconds,'process_group_actions':False})
            if name=='native':write(OWN/'attempt/native-terminal.json',{'exit':None,'shell_returncode':child.returncode,'termination':'EIGHT_HOUR_SUPERVISOR_DEADLINE','elapsed_seconds':time.monotonic()-start})
            child=None
            raise
    child=None
    return code
try:
    prior=Path('/srv/android/asus-combined-build-execution-r2')
    prior_failure=read(prior/'attempt/FAILED.json')
    need(prior_failure['type']=='TimeoutExpired','Unexpected r2 terminal state; reconcile before launch')
    rows=related(prior,Path(plan['aosp']))
    write(OWN/'attempt/r2-terminal-lineage.json',{'r2_failure':prior_failure,'r2_driver_sha256':sha(prior/'scripts/execute.py'),'identity_basis':['owned-prefix-command-or-cwd','owned-log-descriptor','same-source-tree-native-engine','actual-parent-child-closure'],'actual_related_processes':rows,'live_related_processes':[r for r in rows if r['state']!='Z'],'lock_alone_used_as_proof':False,'historical_r2_pid_was_not_recorded':True})
    need(not [r for r in rows if r['state']!='Z'],'Live related r2/native process: no launch or blind kill; reconcile actual receipt handles')
    old=[]
    for path in ['/srv/android/asus-r9-postbuild-validation-r2/validation/system-partition.raw','/srv/android/asus-root-enabled-incremental-r1/host-r2/validation/system-partition.raw']:
        p=Path(path);st=p.stat();need(st.st_mode&0o222==0,'Old raw must remain readonly')
        old.append({'path':path,'bytes':st.st_size,'inode':st.st_ino,'mtime_ns':st.st_mtime_ns,'mode':st.st_mode})
    write(OWN/'attempt/old-raw-stat-pins.json',old)
    preserved={}
    for name in ('r1','r2'):
        p=Path('/srv/android/asus-combined-build-execution-'+name)
        preserved[name]={str(f.relative_to(p)):sha(f) for f in [p/'attempt/FAILED.json',p/'final-report.json'] if f.exists()}
    write(OWN/'attempt/preserved-prior-receipts.json',preserved)
    write(OWN/'inputs/plan.json',plan)
    write(OWN/'attempt/started.json',{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'original_lock_inode':15018964,'native_jobs':8,'native_timeout_seconds':28800,'reported_autostop_utc':'2026-11-07T14:52:00Z','autostop_verified_or_modified':False,'source_writes':[],'cache_clean_touch_or_forced_rebuild':False,'source_sweep_or_tests':False,'authorization':'Parent explicitly authorizes fresh r3 m -j8 continuation and unlimited native/host AS; r1/r2 results remain unchanged'})
    write(OWN/'attempt/native-consumed.json',{'command':['m','-j8','systemimage','bootimage'],'lunch':'lineage_p00a-trunk_staging-userdebug','once':True})
    print('r2 actual related lineage terminal; fresh SSH native and host AS unlimited; r3 -j8 eight-hour build starting',flush=True)
    code=run(['/bin/bash',OWN/'scripts/build.sh'],'native.log','native',28800)
    actual=read(OWN/'attempt/m-exit.json') if (OWN/'attempt/m-exit.json').exists() else None
    native=actual['exit'] if actual else None
    write(OWN/'attempt/native-terminal.json',{'exit':native,'wrapper_exit':code,'actual_m_exit_receipt':actual,'elapsed_seconds':time.monotonic()-start,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
    print(json.dumps({'native_exit':native,'wrapper_exit':code}),flush=True)
    need(native==0 and code==0,'Native command did not succeed; preserve exact first error and do not retry')
    host=run([sys.executable,'-B',OWN/'scripts/postbuild.py'],'postbuild-r1.log','host-validation',28800)
    need(host==0,'Host postbuild failed; preserve artifacts/logs; no native repeat')
    for row in old:
        st=Path(row['path']).stat();need((st.st_size,st.st_ino,st.st_mtime_ns,st.st_mode)==(row['bytes'],row['inode'],row['mtime_ns'],row['mode']),'Old raw metadata changed')
    for name,pins in preserved.items():
        p=Path('/srv/android/asus-combined-build-execution-'+name)
        need(all(sha(p/k)==v for k,v in pins.items()),'Prior failed receipt changed')
    write(OWN/'attempt/complete.json',{'native_exit':native,'critical_postbuild_exit':host,'elapsed_seconds':time.monotonic()-start,'critical_receipt_sha256':sha(OWN/'critical-checks.json'),'physical_boot_verified':False,'whole_os_flash_go':False})
    print((OWN/'attempt/complete.json').read_text(),flush=True)
except BaseException as e:
    with (OWN/'attempt/failure.log').open('x') as f:traceback.print_exc(file=f)
    write(OWN/'attempt/FAILED.json',{'type':type(e).__name__,'error':str(e),'phase':phase,'elapsed_seconds':time.monotonic()-start,'native_repeat_allowed':False,'flash_go':False})
    raise
