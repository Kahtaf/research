from pathlib import Path
import subprocess
A=Path('/srv/android/lineage24');R=Path('/srv/android/asus-hardware-completeness-audit/public-selected')
print('Public selected HALs',list(str(p) for p in R.glob('*sensors*')))
for p in R.glob('*sensors*'):
 print(subprocess.run(['readelf','-Ws',str(p)],capture_output=True,text=True).stdout[-7000:])
for p in [A/'hardware/libhardware/modules/sensors/multihal.h',A/'hardware/libhardware/include_all/hardware/sensors.h']:
 print('FILE',p)
 for line in p.read_text().splitlines():
  if 'CONFIG_FILE_PATH' in line:print(line)
