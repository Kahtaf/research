from pathlib import Path
import os,json,stat,hashlib,subprocess as s,datetime
R=Path('/srv/android/asus-vendor-bpf-load-compat-20261107');assert R.is_dir()
for d in ['inputs','source','evidence','tmp']: (R/d).mkdir(exist_ok=True)
raw=Path('/srv/android/asus-radio-trigger-build-r4/system-partition.raw');boot=Path('/srv/android/asus-radio-trigger-build-r4/checks/r3/UNTESTED-combined-MTKBOOT.img')
def identity(p):
 x=p.stat();return dict(path=str(p),dev=x.st_dev,inode=x.st_ino,bytes=x.st_size,mtime_ns=x.st_mtime_ns,ctime_ns=x.st_ctime_ns,mode=oct(stat.S_IMODE(x.st_mode)))
report=Path('/srv/android/asus-radio-trigger-build-r4/final-report.json');assert hashlib.sha256(report.read_bytes()).hexdigest()=='dd9d8d68ef77a35e188a894193b390d47cf6c10b56b8306909681a5672f80dba'
d=json.loads(report.read_text());assert d['deliverables']['system']['sha256']=='fff09d5ab4e0ca301786830d133106152c4c0aca15a2c49166c28827aa5e3f79';assert raw.stat().st_size==3753902080 and stat.S_IMODE(raw.stat().st_mode)==0o444
prior=json.loads(Path('/srv/android/asus-final-image-startup-20261107/evidence/admission.json').read_text());assert identity(raw)==prior['system'] and identity(boot)==prior['boot'];assert boot.stat().st_size==9242624
a=dict(system=identity(raw),boot=identity(boot),published_system_sha256=d['deliverables']['system']['sha256'],published_report_sha256=hashlib.sha256(report.read_bytes()).hexdigest(),no_fullraw_hash_or_copy=True,utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
(R/'evidence/admission.json').write_text(json.dumps(a,indent=2))
for name,path in [('vendor.fstab','/system/vendor/etc/fstab.mt8163'),('vendor.contexts','/system/vendor/etc/selinux/vendor_file_contexts'),('init.rc','/system/etc/init/hw/init.rc')]:
 p=s.run(['/usr/sbin/debugfs','-R','cat '+path,str(raw)],capture_output=True,timeout=15);assert p.returncode==0 and p.stdout;(R/'inputs'/('original-'+name)).write_bytes(p.stdout)
print(json.dumps(a,indent=2))
# Reuse only the compact generic COW reader, never old payloads.
p=Path('/srv/android/asus-r9-actual-early-runtime-20261106/source/cow_verify.py').read_text().split('# Exact existing genuine xattr storage')[0]
p=p.replace("R=Path('/srv/android/asus-r9-actual-early-runtime-20261106');I=R/'inputs';E=R/'evidence'","R=Path('/srv/android/asus-vendor-bpf-load-compat-20261107');I=R/'inputs';E=R/'evidence'").replace('/srv/android/asus-r9-postbuild-validation-r2/validation/system-partition.raw',str(raw))
(R/'source/cow.py').write_text(p)
