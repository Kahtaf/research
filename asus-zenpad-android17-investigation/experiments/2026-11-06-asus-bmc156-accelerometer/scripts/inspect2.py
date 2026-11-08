from pathlib import Path
import subprocess
k=Path('/srv/android/asus-build-continuation/kernel');a=Path('/srv/android/lineage24')
for glob in ['drivers/misc/mediatek/sensors-1.0/**/sensor_event*','drivers/misc/mediatek/sensors-1.0/**/accel.h','drivers/misc/mediatek/sensors-1.0/**/cust_acc*','drivers/misc/mediatek/sensors-1.0/**/hwmsen_helper.c','drivers/misc/mediatek/sensors-1.0/**/bma253.c']:
 for p in k.glob(glob):
  if not p.is_file(): continue
  print('\nFILE',p);print(p.read_text() if 'bma253.c' not in str(p) else p.read_text()[-18000:])
for p in [Path('/srv/android/asus-build-continuation/build_combined.sh'),k/'drivers/misc/mediatek/sensors-1.0/Makefile',k/'drivers/misc/mediatek/sensors-1.0/Kconfig',k/'arch/arm64/boot/dts/mediatek/asus-p00a.dts']:
 print('\nFILE',p);print(p.read_text())
print('RECIPES');print(subprocess.run(['find','/srv/android','-maxdepth','3','-iname','*build*sh'],capture_output=True,text=True).stdout)
