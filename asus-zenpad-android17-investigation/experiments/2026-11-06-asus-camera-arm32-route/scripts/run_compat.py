import sys
sys.dont_write_bytecode=True
from pathlib import Path
import importlib.util
r=Path(__file__).resolve().parents[1];base=r.parent
spec=importlib.util.spec_from_file_location('remote',base/'2026-11-06-asus-product-input-build-kit/scripts/remote.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
s='from pathlib import Path\np=Path("/srv/android/asus-camera-arm32-route/compat-out");p.mkdir(exist_ok=True)\n'
for label,rel in [('oem','oem-kernel'),('kernel49','sdk37/kernel/asus/p00a-fd')]:
 for name in ['cam_cal_define.h','cam_cal.h']:
  path=base/'2026-11-06-asus-camera-source-abi-route/fixture'/rel/'drivers/misc/mediatek/cam_cal/inc'/name
  s+='(p/'+repr(label+'_'+name)+').write_text('+repr(path.read_text())+')\n'
s+=(r/'scripts/compat_layout.py').read_text();out=m.run(s);(r/'evidence/compat-layout.txt').write_text(out);print(out[:1300])
