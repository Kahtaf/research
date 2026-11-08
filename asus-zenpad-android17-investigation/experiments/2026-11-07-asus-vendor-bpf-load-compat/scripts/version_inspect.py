from pathlib import Path
import subprocess as s
base=Path('/srv/android/lineage24/packages/modules/Connectivity/bpf/headers/include')
for p in base.rglob('*.h'):
 t=p.read_text()
 if 'isAtLeastKernelVersion' in t:
  print(p)
  for i,l in enumerate(t.splitlines()):
   if any(x in l for x in ['isAtLeastKernelVersion','minSupportedKernelVer','kernelVer =']):print('\n'.join(t.splitlines()[max(0,i-5):i+14]))
print(Path('/srv/android/asus-vendor-bpf-load-compat-20261107/source/Loader.cpp').read_text()[18000:19000])
