from pathlib import Path
import json,os,hashlib,shutil
R=Path('/srv/android/asus-r9-linkerconfig-ownership-fix-20261106');os.environ['TMPDIR']=str(R/'tmp');D=Path('/srv/android/asus-device-product');report={}
for sub in ['revisions/r6','revisions/r7','compatibility/patches','graphics-result-r7/source','graphics-result-r7/inputs']:
 p=D/sub;report[sub]=[x.name for x in p.iterdir()]
for sub in ['compatibility/system-linkerconfig-applied.diff','compatibility/series.json','graphics-result-r7/source-pins.json','graphics-result-r7/manifest.json']:
 p=D/sub;dest=R/'inputs'/sub;dest.parent.mkdir(exist_ok=True,parents=True);shutil.copyfile(p,dest);report[sub]={'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
(R/'evidence/frozen-locations.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));print((D/'compatibility/system-linkerconfig-applied.diff').read_text()[:18000])
