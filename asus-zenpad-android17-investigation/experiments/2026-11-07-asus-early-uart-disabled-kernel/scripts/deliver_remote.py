from pathlib import Path
import base64,hashlib,json,sys
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R.parent/'2026-11-06-asus-product-input-build-kit/scripts'))
from remote import run
image=(R/'artifacts/candidate.img').read_bytes()
pkg=json.loads((R/'evidence/packaging-receipt.json').read_text())
script='''from pathlib import Path
import base64,hashlib,json
R=Path('/srv/android/asus-early-uart-disabled-kernel-20261107')
pkg=PKG
image=base64.b64decode(DATA,validate=True)
full=image+bytes(16740352-len(image))
def rec(x):return dict(bytes=len(x),sha256=hashlib.sha256(x).hexdigest())
assert rec(image)==pkg['image'] and rec(full)==pkg['full_p10']
for name,data in [('candidate.img',image),('candidate.p10.raw',full)]:
 with (R/'artifacts'/name).open('xb') as f:f.write(data)
 assert (R/'artifacts'/name).read_bytes()==data
(R/'evidence/packaging-receipt.json').write_text(json.dumps(pkg,indent=2)+'\\n')
receipt=dict(owned_prefix=str(R),image=rec((R/'artifacts/candidate.img').read_bytes()),full_p10=rec((R/'artifacts/candidate.p10.raw').read_bytes()),actual_readback=True,hardware_contact=False)
(R/'evidence/remote-delivery.json').write_text(json.dumps(receipt,indent=2)+'\\n')
print(json.dumps(receipt))
'''.replace('PKG',repr(pkg)).replace('DATA',repr(base64.b64encode(image).decode()))
result=run(script)
(R/'evidence/remote-delivery.json').write_text(result)
print(result,end='')
