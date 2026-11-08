from pathlib import Path
import remote,json
s=r'''
from pathlib import Path
import json
R=Path('/srv/android/asus-reviewed-build-kit/r9')
r=dict(status='REJECTED_AUDIT_NOT_ADMITTED',reason='.installable_files enumerates potential installables including tests, not actual image selection. Use only selected-lfs-product-audit.json qualification.',old_reader='Read-only SSH/Python worker from preparation/lfs_scope.py; stopping it requires explicit permission because process operations were prohibited.',active_source_mutation=False)
with (R/'evidence/selected-lfs-audit.json').open('x') as f:json.dump(r,f,indent=2);f.write('\n')
print(json.dumps(r,indent=2))
'''
r=remote.run(s);Path('2026-11-06-asus-r9-webview-continuation/evidence/selected-lfs-audit.json').write_text(r);print(r)
