import remote,json
from pathlib import Path
s=r'''
from pathlib import Path
import json,xml.etree.ElementTree as E
A=Path('/srv/android/lineage24');r={}
for p in (A/'.repo/manifests').rglob('*.xml'):
 if '.git' in p.parts:continue
 t=p.read_text();doc=E.fromstring(t)
 rows=[dict(tag=e.tag,attributes=e.attrib) for e in doc if 'chromium-webview' in str(e.attrib) or e.tag in ['include','default','remote']]
 if rows:r[str(p.relative_to(A))]=dict(rows=rows,text=t if 'chromium-webview' in t else None)
r['project_entries']=[l for l in (A/'.repo/project.list').read_text().splitlines() if 'chromium-webview' in l]
r['selected_metadata_dirs']={str(p):[x.name for x in p.iterdir()] for p in [A/'.repo/projects/external',A/'.repo/project-objects'] if p.exists()}
r['readme']=(A/'external/chromium-webview/README').read_text()
print(json.dumps(r,indent=2))
'''
r=remote.run(s);Path('2026-11-06-asus-r9-webview-continuation/evidence/cohort.json').write_text(r);d=json.loads(r);print(json.dumps({k:v for k,v in d.items() if k!='selected_metadata_dirs'},indent=2)[:18000])
