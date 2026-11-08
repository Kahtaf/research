from pathlib import Path
import json,base64,remote
R=Path(__file__).resolve().parents[1]
s=r'''
from pathlib import Path
import json,base64
R=Path('/srv/android/asus-reviewed-build-kit/r9-exec-r1')
files={}
for rel in ['inputs/plan.json','inputs/bpf-classification.json','evidence/map-generation.json','evidence/linux-qa.json','evidence/scope-preservation.json']:
 p=R/rel;files[rel]=base64.b64encode(p.read_bytes()).decode()
m=json.loads((R/'inputs/native-lineage-map.json').read_text())
summary=dict(schema=m['schema'],source_path=str(R/'inputs/native-lineage-map.json'),scope='Compact index only; complete pinned rows/graph/input relations remain VM-side',records=[dict(output=t,kind=r['provenance_kind'],module=r['module'],variant=r['variant'],sha256=r['artifact']['sha256'],bytes=r['artifact']['bytes'],real_mtime_ns=r['artifact']['mtime_ns'],command_hash_hex=r['command_hash_hex'],source_relations=r['source_relations'],phase_path=r['execution']['phase_path'] if r['execution'] else None,runtime_requalification_required=r['runtime_requalification_required']) for t,r in m['records'].items()])
print(json.dumps(dict(files=files,summary=summary)))
'''
d=json.loads(remote.run(s))
for rel,data in d['files'].items():(R/rel).write_bytes(base64.b64decode(data))
(R/'evidence/native-lineage-compact-index.json').write_text(json.dumps(d['summary'],indent=2)+'\n');print('Collected compact plan, classification, QA and 61-row index; no APK or full graph copied')
