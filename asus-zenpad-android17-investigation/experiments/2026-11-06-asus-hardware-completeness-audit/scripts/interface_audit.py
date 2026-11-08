from pathlib import Path
import subprocess,re
A=Path('/srv/android/lineage24');K=A/'kernel/asus/p00a-fd'
for rel,pat in [
 ('drivers/misc/mediatek/accelerometer/accel.c',r'input_report|sensor_event|sensor_attr|accdevnum|accactive|accdelay|accbatch|accflush|misc|minor|read\s*='),
 ('drivers/misc/mediatek/hwmon/sensors_io.h',r'GSENSOR_IOCTL|COMPAT_GSENSOR|MSENSOR_IOCTL'),
 ('drivers/misc/mediatek/sensors-1.0/accelerometer/accel.c',r'input_report|sensor_event|sensor_attr|accdevnum|accactive|accdelay|accbatch|accflush|misc|minor|read\s*='),
 ('drivers/misc/mediatek/sensors-1.0/Makefile',r'.'),
 ('drivers/misc/mediatek/keypad/mtk-kpd.c',r'input->name|input_dev.*name|KEY_POWER|KEY_VOLUME|wakeup|compatible'),
 ('drivers/misc/mediatek/keypad/kpd.c',r'input->name|input_dev.*name|KEY_POWER|KEY_VOLUME|wakeup|compatible'),
 ('arch/arm64/boot/dts/mediatek/asus-p00a.dts',r'keypad|kpd|keymap|wakeup'),
]:
 p=K/rel;print('\nFILE',p)
 if not p.exists():print('ABSENT');continue
 for i,l in enumerate(p.read_text(errors='replace').splitlines(),1):
  if re.search(pat,l):print(i,l)
for rel in ['hardware/interfaces/audio/common/all-versions/default/service/android.hardware.audio.service.rc','hardware/interfaces/sensors/1.0/default/ACCOUNT_REDACTED','hardware/interfaces/camera/provider/2.4/default/ACCOUNT_REDACTED']:
 p=A/rel;print('\nFILE',p);print(p.read_text())
root=Path('/srv/android/asus-hardware-completeness-audit/public-selected')
for arch in ['lib','lib64']:
 for name in ['hw_audio.primary.mt8163.so','hw_sensors.mt8163.so','hw_camera.mt8163.so']:
  p=root/(arch+'_'+name)
  print('\nMODULE',p)
  r=subprocess.run(['readelf','-Ws',str(p)],capture_output=True,text=True)
  for l in r.stdout.splitlines():
   if ' HMI' in l:print(l)
  strings=[s.decode() for s in re.findall(rb'[\x20-\x7e]{5,}',p.read_bytes())]
  for s in strings:
   if re.search(r'Audio_.*(Switch|Mux)|^PCM|^hw:|mt-soc|^acc(el|batch|flush|delay)|sensors-1.0|batch_input|^accelerometer$|^m_acc',s):print(s)
