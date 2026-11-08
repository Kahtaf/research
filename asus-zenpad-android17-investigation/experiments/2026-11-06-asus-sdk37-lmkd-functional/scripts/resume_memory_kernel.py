from pathlib import Path
import subprocess as s,os,fcntl,resource,json,time,datetime,hashlib
R=Path('/srv/android/asus-sdk37-lmkd-functional');O=R/'kernel-memory-r1';S=O/'resume-r1';S.mkdir();lock=open(R/'kernel-build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});os.nice(10);resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(1800,1800))
cmd=json.loads((O/'commands.json').read_text())[-1];assert cmd[-1]=='Image';assert str(O/'source') in cmd;assert 'O='+str(O/'out') in cmd
(S/'command.json').write_text(json.dumps(cmd,indent=2));t=time.monotonic();timed=False
with (S/'Image.log').open('w') as f:
 p=s.Popen(cmd,stdout=f,stderr=s.STDOUT);(S/'started.json').write_text(json.dumps({'pid':p.pid,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'lock':str(R/'kernel-build.lock'),'product_lock_touched':False,'affinity':list(os.sched_getaffinity(0)),'address_space_limit':1024**3,'nice':10}))
 try:code=p.wait(timeout=1800)
 except s.TimeoutExpired:p.terminate();code=p.wait(timeout=30);timed=True
files=[O/'out/.config',O/'out/arch/arm64/boot/Image'];(S/'status.json').write_text(json.dumps({'returncode':code,'timeout':timed,'seconds':time.monotonic()-t,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':{str(f.relative_to(O)):{'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in files if f.exists()}},indent=2))
