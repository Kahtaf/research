from pathlib import Path
import re,json,os,subprocess
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
a=Path('/srv/android/lineage24'); root=Path('/srv/android/asus-minimal-audio-hal-20261106');root.mkdir(exist_ok=True)
f=a/'out/soong/build.lineage_p00a.ninja'
blocks=[];block=[]
for line in f.open():
 if line.startswith(('build ','rule ')):
  if block and any('audio.primary.default' in x or ('libtinyalsa' in x and 'build ' in x) for x in block[:1]): blocks.append(''.join(block))
  block=[line]
 else:block.append(line)
print(''.join(blocks))
print('DEPS')
for pat in ['out/soong/.intermediates/external/tinyalsa/libtinyalsa/android_arm64*/*','out/soong/.intermediates/hardware/libhardware/modules/audio/audio.primary.default/android_vendor_arm64*/*']:
 for p in a.glob(pat):print(p,p.stat().st_size)
img='/srv/android/asus-stock-system-backup/20261106T172146Z-89fc7700813aad85/system.img'
for path in ['/etc/audio_policy_configuration.xml','/vendor/etc/audio_device.xml','/vendor/etc/audio_policy.conf','/vendor/etc/audio_param']:
 r=subprocess.run(['debugfs','-R',('ls -p ' if path.endswith('audio_param') else 'cat ')+path,img],capture_output=True,text=True)
 print('STOCK_PATH',path);print(r.stdout)
 if not path.endswith('audio_param'):(root/(Path(path).name)).write_text(r.stdout)
