"""Fresh SSH original-lock reacquisition after r3's host receipt capture failed."""
from pathlib import Path
import os,sys,resource
KIT=Path('/srv/android/asus-reviewed-build-kit/r9-exec-r1')
sys.path.insert(0,str(KIT/'scripts'))
from integrate import read,acquire
OWN=Path('/srv/android/asus-radio-trigger-build-r4')
assert resource.getrlimit(resource.RLIMIT_AS)==(resource.RLIM_INFINITY,resource.RLIM_INFINITY)
lock=acquire(read(OWN/'inputs/base-plan.json'))
assert os.fstat(lock.fileno()).st_ino==15018964
os.set_inheritable(lock.fileno(),True)
env=dict(os.environ,REVIEWED_BUILD_LOCK_FD=str(lock.fileno()))
os.execve(sys.executable,[sys.executable,'-B',str(OWN/'scripts/execute.py')],env)
