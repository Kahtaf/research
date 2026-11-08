from pathlib import Path
import os,resource,subprocess,json,base64,hashlib
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
a=Path('/srv/android/lineage24');k=Path('/srv/android/asus-build-continuation/kernel');s=Path('/srv/android/asus-minimal-audio-hal-20261106')
files=[k/'include/sound/mt_soc_audio.h',Path('/srv/android/asus-build-continuation/integration-r5/resolved.config')]
for root in ['out/soong/.intermediates/bionic/libc/libc','out/soong/.intermediates/bionic/libm/libm','out/soong/.intermediates/bionic/libdl/libdl','out/soong/.intermediates/bionic/libc/crtbegin_so','out/soong/.intermediates/bionic/libc/crtend_so']:
 for p in (a/root).glob('android_vendor_arm64*/**/*'):
  if p.is_file() and p.suffix in ['.so','.o']:print('LINK',p,p.stat().st_size)
img='/srv/android/asus-stock-system-backup/20261106T172146Z-89fc7700813aad85/system.img'
p=s/'AudioParamOptions.xml';r=subprocess.run(['debugfs','-R','cat /vendor/etc/audio_param/AudioParamOptions.xml',img],capture_output=True,check=True);p.write_bytes(r.stdout);files.append(p)
files += [s/'audio_device.xml',s/'audio_policy_configuration.xml',s/'audio_policy.conf']
for p in files:
 print('SOURCEJSON',json.dumps({'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'data':base64.b64encode(p.read_bytes()).decode()}))
