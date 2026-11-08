from pathlib import Path
import subprocess
K=Path('/srv/android/asus-bmc156-accelerometer-r1/kernel');A=Path('/srv/android/lineage24')
for g in ['drivers/misc/mediatek/sensors-1.0/**/sensor_attr.c','drivers/misc/mediatek/sensors-1.0/**/cust_acc.c']:
 for p in K.glob(g):print('\nFILE',p,'\n',p.read_text())
for p in [A/'hardware/libhardware/include_all/hardware/sensors.h',A/'hardware/libhardware/include/hardware/sensors.h']:
 if p.exists():print('\nFILE',p,'\n',p.read_text())
print(subprocess.run(['ls','/srv/android/asus-android17-runtime-prereqs/inputs/root/system/lib64'],capture_output=True,text=True).stdout)
