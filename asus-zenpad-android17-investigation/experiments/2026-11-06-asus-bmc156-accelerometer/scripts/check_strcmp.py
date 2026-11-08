from pathlib import Path
import subprocess
for p in ['/srv/android/asus-bmc156-accelerometer-r1/sdk/lib/libc.so','/srv/android/asus-bmc156-accelerometer-r1/hal-out/sensors.mt8163.so']:
 print(p)
 print('\n'.join(l for l in subprocess.check_output(['readelf','--dyn-syms','--wide',p],text=True).splitlines() if 'strcmp' in l))
