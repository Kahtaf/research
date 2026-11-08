from pathlib import Path
import subprocess
R=Path('/srv/android/asus-bmc156-accelerometer-r1');K=R/'kernel'
p=K/'drivers/misc/mediatek/sensors-1.0/hwmon/sensor_dts/sensor_dts.c';s=p.read_text();i=s.index('int get_accel_dts_func');print(s[i:s.index('\n}',i)+2])
print(subprocess.run(['diff','-u',str(R/'evidence/physical-r5.config'),str(R/'out/.config')],capture_output=True,text=True).stdout)
print(subprocess.run(['which','qemu-aarch64'],capture_output=True,text=True).stdout)
print(subprocess.run(['ls','/srv/android/asus-android17-runtime-prereqs/inputs/headers'],capture_output=True,text=True).stdout)
