from pathlib import Path
import json,hashlib
O=Path('/srv/android/asus-sdk37-platform-bpf-startup-20261106');a=json.loads((O/'evidence/selection.json').read_text());b=json.loads((O/'evidence/selection-v2.json').read_text());old={x['install_path']:x for x in a['objects']};changes=[]
for x in b['objects']:
 y=old[x['install_path']]
 if x.get('sha256')!=y.get('sha256') or x.get('missing')!=y.get('missing'):changes.append(x['install_path'])
assert not changes,changes
result={'all_captured_object_hashes_and_availability_unchanged':True,'completed_runtime_jobs_reused':True,'corrected_vendor_graph_chain':next(x for x in b['objects'] if '/vendor/' in x['install_path'])}
(O/'evidence/selection-v2-audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
