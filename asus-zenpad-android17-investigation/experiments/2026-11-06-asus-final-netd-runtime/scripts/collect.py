from pathlib import Path
import json,base64,importlib.util
R=Path(__file__).resolve().parent;O=R.parent
spec=importlib.util.spec_from_file_location('remote',R.parents[1]/'2026-11-06-asus-product-input-build-kit/scripts/remote.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
d=json.loads(m.run((R/'audit_export.py').read_text()))
for name,data in d.items():
 p=O/'evidence/remote'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(base64.b64decode(data))
print(json.dumps(json.loads((O/'evidence/remote/evidence/final-audit-owned.json').read_text()),indent=2))
