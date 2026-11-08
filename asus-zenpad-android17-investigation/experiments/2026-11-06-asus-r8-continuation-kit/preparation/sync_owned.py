exec(open('2026-11-06-asus-r8-continuation-kit/preparation/inspect_remote.py').read().split('script=r')[0])
import base64
R=Path('2026-11-06-asus-r8-continuation-kit');payload={}
for folder in ['scripts','tests','inputs']:
 for f in (R/folder).rglob('*'):
  if f.is_file() and '__pycache__' not in f.parts:payload[str(f.relative_to(R))]=base64.b64encode(f.read_bytes()).decode()
print(m.run('payload='+repr(payload)+r'''
from pathlib import Path
import base64,json
R=Path('/srv/android/asus-reviewed-build-kit/r8')
assert not (R/'attempt').exists()
for rel,b in payload.items():
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(base64.b64decode(b))
obsolete=R/'inputs/r7-terminal-log.json'
if obsolete.exists():obsolete.unlink()  # Own unlaunched duplicate only; original r7 logs remain in place.
print(json.dumps(dict(status='OWN_UNLAUNCHED_KIT_UPDATED',files=len(payload))))
'''))
