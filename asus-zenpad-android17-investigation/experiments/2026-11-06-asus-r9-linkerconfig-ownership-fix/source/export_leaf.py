from pathlib import Path
import json,base64,os
R=Path('/srv/android/asus-r9-linkerconfig-ownership-fix-20261106');os.environ['TMPDIR']=str(R/'tmp');names=list((R/'inputs/leaf').glob('*.ninja'))+[R/'evidence/actual-metadata.json',R/'evidence/host-build-profile.json',R/'evidence/host-dependency-acquisition.json'];print(json.dumps({str(p.relative_to(R)):base64.b64encode(p.read_bytes()).decode() for p in names}))
