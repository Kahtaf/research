from pathlib import Path
for r in ['/srv/android/asus-hardware/sources','/srv/android/asus-hardware/downloads','/srv/android/asus-stock-system-backup','/srv/android/asus-build-continuation/integration-r5']:
 print('\nROOT',r)
 p=Path(r)
 for f in p.glob('*'): print(f.name,'DIR' if f.is_dir() else f.stat().st_size)
for r in ['/srv/android/asus-hardware/sources','/srv/android/asus-stock-system-backup']:
 for f in Path(r).glob('*/*'): print(f,'DIR' if f.is_dir() else f.stat().st_size)
