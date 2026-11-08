from pathlib import Path
import json
r=Path('/srv/android/asus-camera-property-map-20261106')
for n in ['commands.json','host-commands.json']:
 p=r/n
 if p.exists():
  x=json.loads(p.read_text());print(n,[(c['rc'],c['argv'][-3:]) for c in x]);print(x[-1]['stderr'][:7000])
