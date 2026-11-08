"""Run the remaining existing host checks under the original lock; never native."""
from pathlib import Path
import os,sys,json,resource,subprocess,time
OWN=Path('/srv/android/asus-radio-trigger-build-r4');KIT=Path('/srv/android/asus-reviewed-build-kit/r9-exec-r1')
sys.path.insert(0,str(KIT/'scripts'))
from integrate import read,acquire,write,need
from lineage import related,stop_owned_handles
lock=acquire(read(OWN/'inputs/base-plan.json'));need(os.fstat(lock.fileno()).st_ino==15018964,'Wrong lock')
need(resource.getrlimit(resource.RLIMIT_AS)==(resource.RLIM_INFINITY,resource.RLIM_INFINITY),'Host AS capped')
rows=related(OWN,Path('/srv/android/lineage24'));names={'soong_ui','soong_build','ckati','ninja','ninja-build','siso'}
need(not [r for r in rows if r['state']!='Z' and r['comm'] in names],'Related native engine active; no host continuation')
env=dict(os.environ,REVIEWED_BUILD_LOCK_FD=str(lock.fileno()))
start=time.monotonic()
with (OWN/'logs/postbuild-r2.log').open('xb') as log:
 child=subprocess.Popen([sys.executable,'-B',str(OWN/'scripts/postbuild_r2.py')],stdout=log,stderr=subprocess.STDOUT,cwd=OWN,env=env,pass_fds=(lock.fileno(),))
 try:code=child.wait(timeout=28800)
 except subprocess.TimeoutExpired:
  stopped=stop_owned_handles(OWN,child);write(OWN/'host-r2-timeout.json',{'exact_owned_handles':stopped,'deadline_seconds':28800});raise
write(OWN/'host-r2-terminal.json',{'exit':code,'native_repeated':False,'elapsed_seconds':time.monotonic()-start,'original_lock_inode':15018964})
print(json.dumps(read(OWN/'host-r2-terminal.json')),flush=True)
raise SystemExit(code)
