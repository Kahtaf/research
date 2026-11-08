from pathlib import Path
import subprocess as s,gzip,json
p=Path('/srv/android/asus-reviewed-build-kit/r8/attempt/native-evidence/bootimage/verbose.log.gz');print('LOG',p.exists())
if p.exists():
 with gzip.open(p,'rt',errors='replace') as f:
  for line in f:
   if 'filterPowerSupplyEvents.c' in line and ('clang' in line or 'PWD=' in line):print(line[:14000])
p=Path('/srv/android/lineage24/out/soong/build.lineage_p00a.ninja');print(s.run(['rg','-n','-C','3','filterPowerSupplyEvents.c',str(p)],capture_output=True,text=True).stdout[:16000])
