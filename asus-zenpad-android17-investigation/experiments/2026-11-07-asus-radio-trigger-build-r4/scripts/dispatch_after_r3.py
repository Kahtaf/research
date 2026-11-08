"""Post-native handoff only; preserve r3 identities and continuous original flock."""
from pathlib import Path
import os,json,subprocess,resource,datetime,hashlib
R3=Path('/srv/android/asus-combined-build-execution-r3')
R4=Path('/srv/android/asus-radio-trigger-build-r4')
read=lambda p:json.loads(p.read_text())
assert read(R3/'attempt/native-terminal.json')['exit']==0
assert read(R3/'attempt/m-exit.json')['exit']==0
fd=int(os.environ['REVIEWED_BUILD_LOCK_FD']);assert os.fstat(fd).st_ino==15018964
assert resource.getrlimit(resource.RLIMIT_AS)==(resource.RLIM_INFINITY,resource.RLIM_INFINITY)
assert not (R3/'raw-reservation.json').exists(),'R3 materialization already started: preserve and reconcile, never silently substitute'
assert not (R4/'dispatch.json').exists(),'Forward dispatch consumed'
(R4/'logs').mkdir(exist_ok=True)
with (R4/'logs/supervisor.log').open('xb') as log:
 child=subprocess.Popen(['python3','-B',str(R4/'scripts/execute.py')],stdout=log,stderr=subprocess.STDOUT,pass_fds=(fd,),env=dict(os.environ),cwd=R4)
 stat=(Path('/proc')/str(child.pid)/'stat').read_text().split(') ',1)[1].split()
 receipt={'status':'FORWARD_SUPERVISOR_LAUNCHED_VALIDATION_PENDING','r3_native_exit':0,'r4_prefix':str(R4),'r4_supervisor_pid':child.pid,'r4_start_ticks':int(stat[19]),'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'original_lock_inode':15018964,'continuous_lock_fd_inherited':True,'r3_raw_created':False,'r3_image_validation_claimed':False}
 with (R4/'dispatch.json').open('x') as f:json.dump(receipt,f,indent=2);f.write('\n')
 with (R3/'critical-checks.json').open('x') as f:json.dump(dict(receipt,status='R3_NATIVE_SUCCESS_VALIDATION_DEFERRED_TO_R4'),f,indent=2);f.write('\n')
 with (R3/'attempt/radio-forward-handoff.json').open('x') as f:json.dump(receipt,f,indent=2);f.write('\n')
 print(json.dumps(receipt),flush=True)
