from pathlib import Path
import os,hashlib,json,base64,fcntl,stat,datetime,signal
signal.alarm(60)
sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(PAYLOAD)==PAYLOAD_SHA
payload=json.loads(PAYLOAD)
active=Path('/srv/android/lineage24')
owned=Path('/srv/android/asus-device-profile-integration-20261106');owned.mkdir()
lock_path=Path('/srv/android/asus-device-product/logs/full-product-build.lock')
allowed={'device/asus/p00a/device.mk','device/asus/p00a/manifest.xml','device/asus/p00a/sepolicy/vendor/file_contexts','device/asus/p00a/vintf-legacy/Android.bp','device/asus/p00a/vintf-legacy/PROVENANCE.json','device/asus/p00a/vintf-legacy/compatibility_matrix.p00a-p.xml','device/asus/p00a/vintf-legacy/p-4.9/android-base.config','device/asus/p00a/vintf-legacy/p-4.9/android-base-arm.config','device/asus/p00a/vintf-legacy/p-4.9/android-base-arm64.config','device/asus/p00a/vintf-legacy/p-4.9/android-base-conditional.xml'}
assert {f['path'] for f in payload['files']}==allowed and len(payload['files'])==len(allowed)
def nonsymlink(p):
 assert not any(x.is_symlink() for x in (p,*p.parents)),str(p)
def save(name,value):
 p=owned/name;t=p.with_name(p.name+'.pending')
 with t.open('w') as out:json.dump(value,out,indent=2,sort_keys=True);out.write('\n');out.flush();os.fsync(out.fileno())
 os.replace(t,p);fd=os.open(p.parent,os.O_RDONLY)
 try:os.fsync(fd)
 finally:os.close(fd)
record={'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PREPARING','payload_sha256':PAYLOAD_SHA,'source_root':str(active),'lock_inode':15018964,'changes':[],'native_build_started':False,'out_or_kernel_changed_by_script':False,'device_contacted':False}
try:
 with lock_path.open('r+b') as lock:
  assert os.fstat(lock.fileno()).st_ino==15018964
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  root_mk=active/'device/asus/p00a/lineage_p00a.mk';nonsymlink(root_mk);assert sha(root_mk.read_bytes())==payload['root_mk_sha256']
  modes={}
  for f in payload['files']:
   p=active/f['path'];nonsymlink(p);data=base64.b64decode(f['data_base64'],validate=True);assert len(data)==f['bytes'] and sha(data)==f['after_sha256']
   if f['before_sha256'] is None:assert not p.exists();modes[f['path']]=0o644
   else:
    assert p.is_file() and sha(p.read_bytes())==f['before_sha256'];s=p.stat();assert s.st_uid==os.getuid();modes[f['path']]=stat.S_IMODE(s.st_mode)
    backup=owned/'preimages'/f['path'];backup.parent.mkdir(parents=True,exist_ok=True);backup.write_bytes(p.read_bytes())
  record['status']='PREIMAGES_VERIFIED';save('journal.json',record)
  for f in payload['files']:
   p=active/f['path'];p.parent.mkdir(parents=True,exist_ok=True);nonsymlink(p)
   if f['before_sha256'] is None:assert not p.exists()
   else:assert sha(p.read_bytes())==f['before_sha256']
   tmp=p.with_name('.'+p.name+'.asus-device-profile-stage')
   with tmp.open('xb') as out:out.write(base64.b64decode(f['data_base64']));out.flush();os.fchmod(out.fileno(),modes[f['path']]);os.fsync(out.fileno())
   os.replace(tmp,p);fd=os.open(p.parent,os.O_RDONLY)
   try:os.fsync(fd)
   finally:os.close(fd)
   assert sha(p.read_bytes())==f['after_sha256'];record['changes'].append({k:v for k,v in f.items() if k!='data_base64'});record['status']='APPLYING';save('journal.json',record)
  assert sha(root_mk.read_bytes())==payload['root_mk_sha256']
  for f in payload['files']:assert sha((active/f['path']).read_bytes())==f['after_sha256']
  record.update(status='SOURCE_INTEGRATED_NATIVE_BUILD_PENDING',completed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),root_mk_unchanged=True,all_postimages_verified=True)
  save('journal.json',record)
except Exception as error:
 record.update(status='REFUSED_OR_PARTIAL_SOURCE_INTEGRATION',error_type=type(error).__name__,error=str(error));save('failure.json',record);raise
print(json.dumps(record))
