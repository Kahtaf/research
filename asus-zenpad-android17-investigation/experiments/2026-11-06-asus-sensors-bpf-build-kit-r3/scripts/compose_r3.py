"""One-time isolated r3 composition. Never writes active source/out or prior revisions."""
from pathlib import Path
import base64, hashlib, json
from remote import run
ROOT=Path(__file__).resolve().parents[1]
if (ROOT/'evidence/composition-r3.json').exists():raise RuntimeError('Preserve completed composition; no retry')
payload={}
for folder in ['inputs/sensor-source']:
 for p in (ROOT/folder).rglob('*'):
  if p.is_file():payload[str(p.relative_to(ROOT))]=base64.b64encode(p.read_bytes()).decode()
for name in ['bmc156-pre-post.json','bmc156-source-pins.json','firstboot-parent-acceptance.json','bmc156-from-r5.patch','bpfloader.rs','platform-bpf.patch','PublicVolume.cpp','vold.patch','bpf-supplement-manifest.json','bpf-qualified-selection.json','vold-qualified-receipt.json']:
 payload['inputs/'+name]=base64.b64encode((ROOT/'inputs'/name).read_bytes()).decode()
script=(ROOT/'scripts/remote_compose.py').read_text()
result=json.loads(run('PAYLOAD='+repr(payload)+'\n'+script))
for rel,data in result.pop('exports').items():
 p=ROOT/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(base64.b64decode(data))
(ROOT/'evidence/composition-r3.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
