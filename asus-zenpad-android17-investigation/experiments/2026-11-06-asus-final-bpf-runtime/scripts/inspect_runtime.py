from pathlib import Path
import subprocess as s,json
O=Path('/srv/android/asus-final-bpf-runtime-20261106');p=O/'capture/root/system/vendor/etc/bpf/filterPowerSupplyEvents.o'
print('VENDOR',p.exists())
if p.exists():print(s.run(['readelf','-a',str(p)],capture_output=True,text=True).stdout[:18000])
for p in (O/'capture/root').rglob('*'):
 if p.is_file() and '/bin/' in str(p):print('DYNAMIC',str(p),s.run(['readelf','-d',str(p)],capture_output=True,text=True).stdout[:2000])
print('RUNTIME_LIBS',[str(p.relative_to(Path('/srv/android/asus-sdk37-platform-bpf-startup-20261106/inputs/runtime-root-r2'))) for p in Path('/srv/android/asus-sdk37-platform-bpf-startup-20261106/inputs/runtime-root-r2').rglob('*') if p.is_file() and not ('/etc/bpf/' in str(p))])
