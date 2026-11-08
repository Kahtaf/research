"""Read-only local digest verification; does not execute any binary or build."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[1]
def pin(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024**2),b''):h.update(b)
    return dict(bytes=p.stat().st_size,sha256=h.hexdigest())
count=0
for file in ['SOURCE_PINS.json','ARTIFACTS.json','OUTPUT_PINS.json']:
    for name,expected in json.loads((R/file).read_text()).items():
        assert pin(R/name)==expected,(file,name);count+=1
before=json.loads((R/'evidence/original-files-before.json').read_text())
assert all(pin(R.parent/name)==expected for name,expected in before.items())
assert pin(R/'artifacts/UNQUALIFIED-future5role-policy')==dict(bytes=390437,sha256='3d982859fdbf06336d6274e7e700ca64a2551effd769a8cb119b4fed97388815')
assert not list(R.rglob('terminal_manifest_binding.h'))
assert not list((R/'artifacts').rglob('*.img'))
print('DELIVERY_PINS_PASS',count,'entries;',len(before),'originals unchanged')
