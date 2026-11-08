from pathlib import Path
for root in ['/srv/android/asus-hardware','/srv/android/asus-android17','/srv/android/asus-device-product','/srv/android/reference-kernel']:
 p=Path(root); print('\nROOT',root)
 for f in p.iterdir(): print(f.name, 'DIR' if f.is_dir() else f.stat().st_size)
for root in ['/srv/android/lineage24/device/asus/p00a','/srv/android/asus-build-continuation/integration-r5/product-device']:
 p=Path(root); print('\nPRODUCT',root)
 for f in p.rglob('*'):
  if f.is_file() and f.suffix in ['.mk','.xml','.rc','.bp'] and not any(x in f.parts for x in ['prebuilt','.git']):
   print('\nFILE',f); print(f.read_text(errors='replace')[:28000])
