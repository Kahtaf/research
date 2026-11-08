from pathlib import Path
import os,json
R=Path('/srv/android/asus-r9-linkerconfig-ownership-fix-20261106');os.environ['TMPDIR']=str(R/'tmp');d={}
for path in ['/srv/android/asus-product-integration-staging','/srv/android/asus-product-integration-staging/r6','/srv/android/asus-reviewed-build-kit','/srv/android/asus-runtime-prerequisite-build-r2','/srv/android/asus-runtime-prerequisite-build-r1','/srv/android/asus-firstboot-runtime/inputs','/srv/android/asus-genuine-service-runtime/inputs']:
 p=Path(path);d[path]=[x.name for x in p.iterdir()] if p.is_dir() else None
print(json.dumps(d,indent=2));(R/'evidence/locations.json').write_text(json.dumps(d,indent=2))
