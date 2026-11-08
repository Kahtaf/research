from pathlib import Path
import subprocess
A=Path('/srv/android/lineage24')
for n in ['system/sepolicy/vendor/file_contexts','system/sepolicy/private/file_contexts','system/sepolicy/public/hal_sensors.te','system/sepolicy/vendor/hal_sensors_default.te','system/sepolicy/public/file.te']:
 p=A/n
 if p.exists():
  print('FILE',n)
  for line in p.read_text().splitlines():
   if 'sensor' in line: print(line)
print('multihal header')
p=A/'hardware/libhardware/modules/sensors/multihal.h'
for l in p.read_text().splitlines():
 if 'CONFIG_FILE' in l:print(l)
# Public OEM ELF symbol metadata only.
p=Path('/srv/android/asus-hardware-completeness-audit/public-selected/lib64_hw_sensors.mt8163.so')
for l in subprocess.check_output(['readelf','-Ws',str(p)],text=True).splitlines():
 if any(w in l for w in ['SensorList','sSensorList','sensor_list','HMI']):print(l)
