"""One authorized ordinary cached build, unlimited AS, eight-hour native deadline."""
from pathlib import Path
import datetime,json,os,resource,subprocess,sys,time,traceback
OWN=Path('/srv/android/asus-radio-trigger-build-r4')
KIT=Path('/srv/android/asus-reviewed-build-kit/r9-exec-r1')
sys.path.insert(0,str(KIT/'scripts'))
from integrate import read,write,sha,need,acquire
from lineage import related,stop_owned_handles
plan=read(OWN/'inputs/base-plan.json')
start=time.monotonic(); child=None; phase=None
os.environ.update(PYTHONDONTWRITEBYTECODE='1',GIT_OPTIONAL_LOCKS='0')
inherited_fd=int(os.environ['REVIEWED_BUILD_LOCK_FD'])
lock=os.fdopen(os.dup(inherited_fd),'rb')
import fcntl
fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
need(os.fstat(lock.fileno()).st_ino==15018964,'Wrong original lock inode')
need(not (OWN/'attempt').exists(),'Consumed attempt: refuse repeat')
(OWN/'attempt').mkdir();(OWN/'logs').mkdir(exist_ok=True)
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
    prior=Path('/srv/android/asus-combined-build-execution-r3')
    terminal=read(prior/'attempt/native-terminal.json');m_exit=read(prior/'attempt/m-exit.json')
    need(terminal['exit']==0 and m_exit['exit']==0,'No durable genuine r3 native exit0; do not change source or launch')
    old_handle=read(prior/'attempt/native-handle.json')
    from lineage import snapshot
    current=snapshot().get(old_handle['pid'])
    need(not current or current['start_ticks']!=old_handle['start_ticks'] or current['state']=='Z','Actual r3 native shell handle still live')
    rows=related(prior,Path(plan['aosp']));native_names={'soong_ui','soong_build','ckati','ninja','ninja-build','siso'}
    live=[]
    for row in rows:
        if row['state']=='Z':continue
        reasons=[]
        if row['comm'] in native_names:reasons.append('live-related-native-engine')
        try:
            for fd in (Path('/proc')/str(row['pid'])/'fd').iterdir():
                try:target=os.readlink(fd)
                except OSError:continue
                if target==str(prior/'logs/native.log'):reasons.append('r3-native-log-open');break
        except (FileNotFoundError,PermissionError):pass
        if reasons:live.append(dict(row,blocking_reasons=reasons))
    write(OWN/'attempt/prior-native-lineage.json',{'r3_native_terminal':terminal,'r3_actual_m_exit':m_exit,'r3_recorded_handle':old_handle,'live_related_native_processes':live,'continuous_inherited_lock_inode':15018964})
    need(not live,'Related r3 native lineage is live; no source change, new launch or blind signal')
    pins=read(OWN/'inputs/radio-pins.json');source=Path(plan['device'])/'radio/init.p00a-radio.rc'
    need(sha(OWN/'inputs/radio-trigger.patch')==pins['patch_sha256']=='1a3e52ee01688248ccf5c88ff4b7100ce517511c6747a07350dfaebf933c3004','Radio patch pin differs')
    need(sha(source)==pins['before_sha256']=='67ebf4f61d77dbc3c05b71b040eb58f5c3fa04f26a7a22b8ca25308de0d13337','Exact radio preimage differs')
    need(source.read_bytes()==(OWN/'inputs/radio-before.rc').read_bytes(),'Exact radio preimage bytes differ')
    need(sha(OWN/'inputs/radio-after.rc')==pins['after_sha256']=='f618fdbaa7d8c659b5edc4dbcf1b21bf30f3525a08c1f88d17ed873b02a23f71','Radio postimage pin differs')
    source.write_bytes((OWN/'inputs/radio-after.rc').read_bytes())
    need(sha(source)==pins['after_sha256'],'Actual radio source integration failed')
    write(OWN/'attempt/source-integration.json',{'path':str(source),'before_sha256':pins['before_sha256'],'after_sha256':sha(source),'patch_sha256':pins['patch_sha256'],'r3_native_exit0_recorded_before_write':True,'only_active_source_delta':'two radio/BT loader property trigger lines','source_expected_map_sha256':sha(OWN/'inputs/expected-product.json'),'runtime_radio_working_claimed':False})
    old=[]
    for path in ['/srv/android/asus-r9-postbuild-validation-r2/validation/system-partition.raw','/srv/android/asus-root-enabled-incremental-r1/host-r2/validation/system-partition.raw']:
        p=Path(path);st=p.stat();need(st.st_mode&0o222==0,'Old raw must remain readonly')
        old.append({'path':path,'bytes':st.st_size,'inode':st.st_ino,'mtime_ns':st.st_mtime_ns,'mode':st.st_mode})
    write(OWN/'attempt/old-raw-stat-pins.json',old)
    preserved={}
    for name in ('r1','r2','r3'):
        p=Path('/srv/android/asus-combined-build-execution-'+name)
        preserved[name]={str(f.relative_to(p)):sha(f) for f in [p/'attempt/FAILED.json',p/'final-report.json',p/'attempt/native-terminal.json',p/'attempt/m-exit.json'] if f.exists()}
    write(OWN/'attempt/preserved-prior-receipts.json',preserved)
    write(OWN/'inputs/plan.json',plan)
    write(OWN/'attempt/integration.json',read(OWN/'attempt/source-integration.json'))
    write(OWN/'attempt/started.json',{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'original_lock_inode':15018964,'native_jobs':8,'native_timeout_seconds':28800,'reported_autostop_utc':'2026-11-07T14:52:00Z','autostop_verified_or_modified':False,'reported_autostop_remaining_seconds_at_record':(datetime.datetime(2026,11,7,14,52,tzinfo=datetime.timezone.utc)-datetime.datetime.now(datetime.timezone.utc)).total_seconds(),'source_writes':['device/asus/p00a/radio/init.p00a-radio.rc'],'cache_clean_touch_or_forced_rebuild':False,'source_sweep_or_tests':False,'authorization':'Parent explicitly authorizes exact radio trigger forward fix only after genuine r3 native exit0, then one j8 ordinary cached continuation; all prior results remain unchanged'})
    write(OWN/'attempt/native-consumed.json',{'command':['m','-j8','systemimage','bootimage'],'lunch':'lineage_p00a-trunk_staging-userdebug','once':True})
    print('Genuine r3 native exit0 and terminal lineage verified; exact two-line radio fix integrated; r4 j8 eight-hour native build starting',flush=True)
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
