from pathlib import Path
import sys,json,base64
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R.parent/'2026-11-06-asus-product-input-build-kit/scripts'))
from remote import run
receipt=json.loads((R/'evidence/packaging-receipt.json').read_text())
encoded=base64.b64encode((R/'artifacts/candidate.img').read_bytes()).decode()
s='''from pathlib import Path
import base64,hashlib,json
R=Path('/srv/android/asus-early-watchdog-handoff-20261107')
assert not (R/'artifacts/candidate.img').exists() and not (R/'artifacts/candidate.p10.raw').exists(),'Existing package delivery refused'
image=base64.b64decode(ENCODED);expected=EXPECTED
rec=lambda d:dict(bytes=len(d),sha256=hashlib.sha256(d).hexdigest())
assert rec(image)==expected['image']
full=image+bytes(16740352-len(image));assert rec(full)==expected['full_p10']
(R/'artifacts/candidate.img').write_bytes(image);(R/'artifacts/candidate.p10.raw').write_bytes(full)
actual=dict(image=rec((R/'artifacts/candidate.img').read_bytes()),full_p10=rec((R/'artifacts/candidate.p10.raw').read_bytes()),full_p10_path=str(R/'artifacts/candidate.p10.raw'),actual_saved_readback=True,device_contacted=False)
assert actual['image']==expected['image'] and actual['full_p10']==expected['full_p10']
(R/'evidence/packaging-receipt.json').write_text(json.dumps(expected,indent=2)+'\\n')
(R/'evidence/remote-package-readback.json').write_text(json.dumps(actual,indent=2)+'\\n')
print(json.dumps(actual))
'''.replace('ENCODED',repr(encoded)).replace('EXPECTED',repr(receipt))
result=json.loads(run(s));(R/'evidence/remote-package-readback.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
