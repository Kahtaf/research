"""Parent-owned targeted native build, continuous original lifecycle lock."""
from pathlib import Path
import datetime,fcntl,hashlib,json,os,subprocess,sys,traceback
R=Path('/srv/android/asus-genuine-service-build-r1')
A=Path('/srv/android/lineage24')
L=Path('/srv/android/asus-device-product/logs')
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(name,value):
 p=R/name
 with p.open('x') as f:
  json.dump(value,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
def native_builds():
 found=[]
 for p in Path('/proc').iterdir():
  if not p.name.isdigit():continue
  try:comm=(p/'comm').read_text().strip();args=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')
  except OSError:continue
  if comm in ('siso','ninja','soong_ui','soong_build','ckati') or (comm=='bash' and 'soong_ui.bash --make-mode' in args):
   found.append(dict(pid=int(p.name),comm=comm,args=args[:300]))
 return found
def sources():
 paths=['device/asus/p00a/AndroidProducts.mk','device/asus/p00a/BoardConfig.mk','device/asus/p00a/device.mk','device/asus/p00a/lineage_p00a.mk','device/asus/p00a/firstboot/firstboot-services.mk','system/vold/model/PublicVolume.cpp','system/memory/lmkd/lmkd.cpp']
 return {n:sha(A/n) for n in paths if (A/n).is_file()}
def main():
 assert Path(__file__).resolve()==R/'supervise.py'
 with (L/'full-product-build.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  assert not native_builds(),native_builds()
  assert (L/'full-build-r5.exit-code').read_text().strip()=='1'
  assert (L/'full-build-r5.finished').is_file()
  assert not (L/'full-build-r5.complete').exists() and not (L/'full-build-r6.started').exists()
  prior={n:(L/n).read_text() for n in ['full-build-r5.started','full-build-r5.finished','full-build-r5.exit-code']}
  before=sources();assert before['system/vold/model/PublicVolume.cpp']=='0e17fccedefabb20e2d8650252af8c765af68378a1d853e0fbaa6a8bd1ea67fd'
  env=dict(os.environ,SERVICE_BUILD_LOCK_FD=str(lock.fileno()),PYTHONDONTWRITEBYTECODE='1')
  started=dict(utc=utc(),supervisor_pid=os.getpid(),lock_inode=os.fstat(lock.fileno()).st_ino,source_pins=before,prior=prior,targets=['apexd','hwservicemanager','keystore2','servicemanager','android.hardware.keymaster@4.0-service','lmkd','com.android.adbd'],jobs=8,source_edits=False,installclean=False,full_image_r6=False)
  put('started.json',started)
  with (R/'native-build.log').open('xb') as log:
   child=subprocess.Popen(['bash',str(R/'build-targets.sh')],cwd=A,env=env,stdout=log,stderr=subprocess.STDOUT,pass_fds=(lock.fileno(),))
   put('native-child.json',dict(utc=utc(),pid=child.pid,supervisor_pid=os.getpid()))
   rc=child.wait()
  after=sources();unchanged=before==after and prior=={n:(L/n).read_text() for n in prior}
  outputs={}
  for name in ['apexd','hwservicemanager','keystore2','servicemanager','lmkd']:
   p=A/'out/target/product/p00a/system/bin'/name
   outputs[str(p)]=dict(exists=p.is_file(),bytes=p.stat().st_size if p.is_file() else None,sha256=sha(p) if p.is_file() else None)
  put('finished.json',dict(utc=utc(),exit_code=rc,selected_active_sources_unchanged=unchanged,source_pins_after=after,prior_r5_markers_unchanged=True,outputs=outputs,full_images_built=False))
  if not unchanged:raise RuntimeError('Selected sources or original markers changed during build')
  return rc
if __name__=='__main__':
 try:sys.exit(main())
 except Exception:
  try:put('supervisor-error.json',dict(utc=utc(),traceback=traceback.format_exc()))
  except OSError:pass
  raise
