from pathlib import Path
import subprocess
A=Path('/srv/android/lineage24')
for p in ['system/sepolicy/vendor/hal_sensors_default.te','hardware/interfaces/sensors/1.0/default/ACCOUNT_REDACTED','hardware/libhardware/hardware.c']:
 f=A/p;print('\nFILE',f);print(f.read_text() if f.exists() else 'absent')
print('policy fixture files')
print(subprocess.run(['find','/srv/android/asus-build-continuation/policy-vendor-r4','-maxdepth','2','-type','f'],capture_output=True,text=True).stdout)
