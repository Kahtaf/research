from pathlib import Path
import remote,json,base64
R=Path(__file__).resolve().parents[1]
s=r'''
from pathlib import Path
import json,base64
R=Path('/srv/android/asus-reviewed-build-kit/r9');names=['inputs/plan.json','inputs/r8-integration.json','inputs/r8-preservation.json','inputs/r9-delta.json','inputs/r8-unapproved-description.json']
print(json.dumps({n:base64.b64encode((R/n).read_bytes()).decode() for n in names}))
'''
for n,b in json.loads(remote.run(s)).items():(R/n).write_bytes(base64.b64decode(b))
print('Collected compact r9 plan, delta, r8 binding and unapproved description; no large payload')
