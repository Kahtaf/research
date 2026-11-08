from pathlib import Path
import sys,json,base64,hashlib
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R.parent/'2026-11-06-asus-product-input-build-kit/scripts'))
from remote import run
s='''from pathlib import Path
import json,base64
R=Path('/srv/android/asus-early-watchdog-handoff-20261107')
assert json.loads((R/'evidence/build-status.json').read_text())['status']=='complete'
files={str(p.relative_to(R)):p for p in (R/'evidence').glob('*.json')}
files.update({str(p.relative_to(R)):p for p in (R/'source').iterdir() if p.is_file()})
files.update({'artifacts/Image.gz-dtb':R/'out/arch/arm64/boot/Image.gz-dtb','artifacts/resolved.config':R/'out/.config'})
assert sum(p.stat().st_size for p in files.values())<32*1024**2
print(json.dumps({n:base64.b64encode(p.read_bytes()).decode() for n,p in files.items()}))
'''
data=json.loads(run(s));total=0;pins={}
for name,encoded in data.items():
 p=R/name;raw=base64.b64decode(encoded);assert not p.exists(),('Refuse duplicate fetch',p)
 p.write_bytes(raw);total+=len(raw);pins[name]=dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
assert total<32*1024**2
(R/'evidence/remote-delivery.json').write_text(json.dumps(dict(total_bytes=total,limit_bytes=32*1024**2,files=pins,full_source_out_log_stay_VM=True),indent=2)+'\n')
print(json.dumps(dict(delivered_bytes=total,files=len(pins))))
