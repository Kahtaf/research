from pathlib import Path
import datetime,fcntl,hashlib,json,os,resource,signal,subprocess,sys,time,traceback
OWN=Path('/srv/android/asus-bpf-name-product-build-20261107')
A=Path('/srv/android/lineage24'); P=A/'out/target/product/p00a'
PRE='4795e5bb1d46187f1aa858ba0703185ff9309dcd6d4fa97f2860b12b357f93b7'
POST='bb8288818619d492a79fe997c902dc9b64fa67f1f04bff4afb2b047b4511dccf'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def write(name,v):
 with (OWN/'evidence'/name).open('x') as f:json.dump(v,f,indent=2);f.write('\n')
def stat(p):
 s=Path(p).stat();return dict(path=str(p),bytes=s.st_size,inode=s.st_ino,dev=s.st_dev,mode=oct(s.st_mode&0o777),mtime_ns=s.st_mtime_ns,ctime_ns=s.st_ctime_ns)
start=time.monotonic();phase='lock';lock=None
try:
 lock=open('/srv/android/asus-device-product/logs/full-product-build.lock','rb')
 assert os.fstat(lock.fileno()).st_ino==15018964,'Original lock inode differs'
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert not (OWN/'evidence/started.json').exists(),'One attempt already consumed'
 assert resource.getrlimit(resource.RLIMIT_AS)==(resource.RLIM_INFINITY,resource.RLIM_INFINITY),'RLIMIT_AS not unlimited'
 os.environ.update(PYTHONDONTWRITEBYTECODE='1',GIT_OPTIONAL_LOCKS='0',REVIEWED_BUILD_LOCK_FD=str(lock.fileno()))
 write('started.json',dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),lock_inode=15018964,rlimit_as=list(resource.getrlimit(resource.RLIMIT_AS)),native_wall_bound_seconds=7200,lunch='lineage_p00a-trunk_staging-userdebug',command=['m','-j8','systemimage'],single_authorized_product_writer=True,other_owner_process_inspection=False))
 old=Path('/srv/android/asus-radio-trigger-build-r4')
 protected=[old/'system-partition.raw',old/'checks/r3/UNTESTED-combined-MTKBOOT.img',P/'boot.img']
 before=[stat(p) for p in protected]
 write('preserved-before.json',before)
 source=A/'system/bpf/loader/Loader.cpp'; patch=OWN/'source/loader-prog-name.patch'
 assert sha(patch)=='e442a96373a2a9a7ec16d59f13315997487935bd074c29f5369a216e15d6993f'
 original=sha(source);assert original in (PRE,POST),'Unknown Loader.cpp source; refuse'
 installed=P/'system/lib64/libbpf_android.so'
 write('library-before.json',dict(path=str(installed),sha256=sha(installed),bytes=installed.stat().st_size))
 phase='source'
 if original==PRE:
  (OWN/'source/Loader.cpp.before').write_bytes(source.read_bytes())
  result=subprocess.run(['patch','--batch','--forward','--no-backup-if-mismatch','-p1','-i',str(patch)],cwd=A,capture_output=True,text=True)
  write('patch-command.json',dict(exit=result.returncode,stdout=result.stdout,stderr=result.stderr))
  assert result.returncode==0,'Patch failed'
 assert sha(source)==POST,'Postimage mismatch'
 write('integration.json',dict(path=str(source),before_sha256=original,after_sha256=sha(source),state='applied-once' if original==PRE else 'already-post',patch_sha256=sha(patch)))
 phase='native'
 with (OWN/'logs/native.log').open('xb') as log:
  child=subprocess.Popen(['/bin/bash',str(OWN/'scripts/build.sh')],stdout=log,stderr=subprocess.STDOUT,pass_fds=(lock.fileno(),),start_new_session=True,env=dict(os.environ))
  try:code=child.wait(timeout=7200)
  except subprocess.TimeoutExpired:
   os.killpg(child.pid,signal.SIGTERM)
   try:child.wait(timeout=30)
   except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
   write('native-terminal.json',dict(exit=None,wrapper_exit=child.returncode,timeout=True,elapsed_seconds=time.monotonic()-start));raise
 actual=json.loads((OWN/'evidence/m-exit.json').read_text()) if (OWN/'evidence/m-exit.json').exists() else None
 write('native-terminal.json',dict(exit=actual['exit'] if actual else None,wrapper_exit=code,timeout=False,elapsed_seconds=time.monotonic()-start))
 assert code==0 and actual and actual['exit']==0,'Native failed; no retry'
 phase='capture'
 result=subprocess.run([sys.executable,'-B',str(OWN/'scripts/capture.py')],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,pass_fds=(lock.fileno(),))
 (OWN/'logs/capture.log').write_text(result.stdout)
 assert result.returncode==0,'Minimal artifact capture failed'
 assert sha(source)==POST
 assert [stat(p) for p in protected]==before,'Protected image metadata changed'
 report=json.loads((OWN/'evidence/artifacts.json').read_text())
 report.update(status='INTEGRATED_NATIVE_EXIT0_MINIMAL_ARTIFACT_CAPTURE_COMPLETE',native_exit=0,source_sha256=sha(source),source_integration=json.loads((OWN/'evidence/integration.json').read_text()),preserved_images_metadata_unchanged=True,old_raw_rehashed=False,elapsed_seconds=time.monotonic()-start,lock_continuous_through_final_capture=True,lock_inode=os.fstat(lock.fileno()).st_ino,whole_framework_or_hardware_success=False,physical_kernel_join_pending=True)
 write('final-report.json',report)
 print(json.dumps(report),flush=True)
except BaseException as e:
 (OWN/'logs/failure.log').write_text(traceback.format_exc())
 write('FAILED.json',dict(phase=phase,error=str(e),type=type(e).__name__,elapsed_seconds=time.monotonic()-start,native_retry=False))
 print(traceback.format_exc(),flush=True)
 raise
finally:
 if lock:lock.close()
