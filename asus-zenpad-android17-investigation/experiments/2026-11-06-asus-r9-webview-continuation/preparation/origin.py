import remote,json
from pathlib import Path
s=r'''
from pathlib import Path
import json
A=Path('/srv/android/lineage24');ps=[A/'.repo/projects/external/chromium-webview.git',A/'.repo/manifests/.git',A/'.repo/manifests.git']
r={}
for p in ps:
 if p.exists():
  r[str(p)]=dict(directory=p.is_dir(),listing=[x.name for x in p.iterdir()] if p.is_dir() else p.read_text())
  if p.is_dir():
   r[str(p)]['files']={n:(p/n).read_text(errors='replace')[:20000] for n in ['config','HEAD','packed-refs','archive.json','source.json','receipt.json'] if (p/n).is_file()}
r['local_manifests']={p.name:p.read_text() for p in (A/'.repo/local_manifests').glob('*.xml')}
r['webview_listing']=[p.name for p in (A/'external/chromium-webview').iterdir()]
r['repo_receipt_names']=[p.name for p in (A/'.repo').iterdir() if p.is_file()]
print(json.dumps(r,indent=2))
'''
r=remote.run(s);Path('2026-11-06-asus-r9-webview-continuation/evidence/origin-metadata.json').write_text(r);print(r)
