from pathlib import Path
import json,os
R=Path('/srv/android/asus-r9-linkerconfig-ownership-fix-20261106');os.environ['TMPDIR']=str(R/'tmp');d={}
for path in ['/srv/android/asus-reviewed-build-kit/r9-exec-r1/inputs/r6-integration.json','/srv/android/asus-reviewed-build-kit/r9-exec-r1/inputs/product-staging.json','/srv/android/asus-reviewed-build-kit/r9-exec-r1/inputs/source-receipt.json']:
 p=Path(path);d[path]=p.read_text() if p.is_file() else None
for path in ['/srv/android/asus-firstboot-parity-continuation','/srv/android/asus-r6-product-build','/srv/android/asus-product-integration-staging/r3','/srv/android/asus-device-product']:
 p=Path(path);d[path]=[x.name for x in p.iterdir()] if p.is_dir() else None
(R/'evidence/source-locations.json').write_text(json.dumps(d,indent=2));print(json.dumps(d,indent=2))
