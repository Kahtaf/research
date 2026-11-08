from pathlib import Path
import gzip
r=Path('/srv/android/asus-reviewed-build-kit/r8/attempt/native-evidence/bootimage');print('FILES',[p.name for p in r.iterdir()])
for p in r.glob('*verbose*'):
 op=gzip.open if p.suffix=='.gz' else open
 with op(p,'rt',errors='replace') as f:
  for line in f:
   if 'filterPowerSupplyEvents.c' in line and 'clang' in line:print('CMD',line[:16000])
p=Path('/srv/android/lineage24/out/soong/build.lineage_p00a.ninja');lines=p.read_text().splitlines()
for i,x in enumerate(lines):
 if 'filterPowerSupplyEvents.c' in x:print('\n'.join(lines[max(0,i-4):i+9]))
