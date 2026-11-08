from pathlib import Path
import subprocess
k=Path('/srv/android/asus-build-continuation/kernel'); a=Path('/srv/android/lineage24')
paths=['drivers/misc/mediatek/sensors-1.0/accelerometer/accel.h','drivers/misc/mediatek/sensors-1.0/accelerometer/accel.c','drivers/misc/mediatek/sensors-1.0/sensor_event.h','drivers/misc/mediatek/sensors-1.0/accelerometer/Makefile','drivers/misc/mediatek/sensors-1.0/accelerometer/Kconfig','drivers/misc/mediatek/sensors-1.0/hwmon/include/cust_acc.h','drivers/misc/mediatek/sensors-1.0/hwmon/hwmsen_helper.c']
for p in paths:
 f=k/p;print('\nFILE',f);print(f.read_text() if f.exists() else 'ABSENT')
for p in ['hardware/interfaces/sensors/1.0/default/Sensors.cpp','hardware/interfaces/sensors/1.0/default/Android.bp']:
 print('\nFILE',a/p);print((a/p).read_text())
print(subprocess.run(['ls','-la','/srv/android/asus-build-continuation'],capture_output=True,text=True).stdout)
