from pathlib import Path
import subprocess as s,shutil,json,hashlib,resource,os,time,datetime,fcntl,re
R=Path('/srv/android/asus-sdk37-lmkd-functional');O=R/'kernel-memory-r1';O.mkdir();log=(O/'supervisor.log').open('w',buffering=1)
os.dup2(log.fileno(),1);os.dup2(log.fileno(),2)
lock=open('/srv/android/asus-device-product/logs/full-product-build.lock','a')
try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
except BlockingIOError:
 (O/'status.json').write_text(json.dumps({'state':'blocked','reason':'product build lock held; no compile started'}));raise SystemExit(2)
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(1800,1800))
P=Path('/srv/android/asus-firstboot-runtime');B=O/'out';K=O/'source';B.mkdir();shutil.copytree(P/'kernel-cpuset-r1',K,ignore=shutil.ignore_patterns('.git'))
old=P/'kernel-build-r7/.config';phys=Path('/srv/android/asus-bmc156-full-kernel-r1/out/.config');assert hashlib.sha256(phys.read_bytes()).hexdigest()=='10b212cabd28aad012582e86c64695ccd450650b4e09ec8da30c21e094f377c2'
shutil.copyfile(old,B/'.config');shutil.copyfile(phys,O/'physical.config');shutil.copyfile(old,O/'virtual-before.config')
# Memory/scheduler features only. Never apply the virtual board config to hardware.
keys=['PSI','PSI_DEFAULT_DISABLED','ZRAM','ZRAM_WRITEBACK','ZRAM_MEMORY_TRACKING','ZSMALLOC','ZSMALLOC_STAT','COMPACTION','CMA','CMA_AREAS','CMA_DEBUG','CMA_DEBUGFS','DMA_CMA','VM_EVENT_COUNTERS','SLUB_DEBUG','SLUB_CPU_PARTIAL','PREEMPT','PREEMPT_NONE','PREEMPT_VOLUNTARY','NO_HZ_IDLE','NO_HZ_FULL','NO_HZ','HZ_PERIODIC','HIGH_RES_TIMERS','CRYPTO_LZ4','CRYPTO_LZO']
t=phys.read_text();requested={};args=[str(K/'scripts/config'),'--file',str(B/'.config')]
for k in keys:
 m=re.search(r'^CONFIG_'+k+r'=(.*)$',t,re.M);v=m[1] if m else 'n';requested[k]=v
 args+=['-e' if v=='y' else '-d' if v=='n' else '--set-val',k]+([] if v in ['y','n'] else [v])
s.run(args,check=True);(O/'requested.json').write_text(json.dumps(requested,indent=2))
cmd=['make','-C',str(K),'O='+str(B),'ARCH=arm64','CROSS_COMPILE=aarch64-linux-gnu-','HOSTCC=gcc','HOSTCXX=g++','KBUILD_BUILD_USER=asus-port','KBUILD_BUILD_HOST=lmkd-functional','KBUILD_BUILD_VERSION=1','KBUILD_BUILD_TIMESTAMP=Fri Nov 6 00:00:00 UTC 2026','-j1']
commands=[];started=time.monotonic();outcome=0
for target in ['olddefconfig','Image']:
 argv=cmd+[target];commands.append(argv);(O/'commands.json').write_text(json.dumps(commands,indent=2))
 with (O/(target+'.log')).open('w') as f:
  p=s.Popen(argv,stdout=f,stderr=s.STDOUT);(O/'child.json').write_text(json.dumps(dict(pid=p.pid,target=target,utc=datetime.datetime.now(datetime.timezone.utc).isoformat())))
  try:outcome=p.wait(timeout=max(1,1800-(time.monotonic()-started)))
  except s.TimeoutExpired:p.kill();outcome=p.wait();break
 if outcome:break
 if target=='olddefconfig':(O/'config-delta.txt').write_text(s.check_output([str(K/'scripts/diffconfig'),str(old),str(B/'.config')],text=True))
files=[B/'.config',B/'arch/arm64/boot/Image'];(O/'status.json').write_text(json.dumps(dict(returncode=outcome,seconds=time.monotonic()-started,finished=datetime.datetime.now(datetime.timezone.utc).isoformat(),files={str(f.relative_to(O)):{'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'bytes':f.stat().st_size} for f in files if f.is_file()}),indent=2));print('terminal',outcome)
