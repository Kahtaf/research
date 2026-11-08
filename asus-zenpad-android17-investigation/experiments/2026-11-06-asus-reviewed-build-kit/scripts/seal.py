"""Local seal; parent must pin the resulting manifest hash outside the kit."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[1]
pins={}
for folder in ['scripts','inputs','tests/packager']:
    for p in sorted((R/folder).rglob('*')):
        if p.is_file() and p.name!='kit-pins.json' and '__pycache__' not in p.parts:
            pins[str(p.relative_to(R))]=hashlib.sha256(p.read_bytes()).hexdigest()
for p in sorted((R/'tests').glob('test_*.py')):pins[str(p.relative_to(R))]=hashlib.sha256(p.read_bytes()).hexdigest()
f=R/'inputs/kit-pins.json';f.write_text(json.dumps(pins,indent=2,sort_keys=True)+'\n')
print(hashlib.sha256(f.read_bytes()).hexdigest(),len(pins),'pinned files')
