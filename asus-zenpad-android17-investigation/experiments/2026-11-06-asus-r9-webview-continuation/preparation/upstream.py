import remote,json
from pathlib import Path
s=r'''
from pathlib import Path
import json,urllib.request,hashlib
A=Path('/srv/android/lineage24');R=Path('/srv/android/asus-reviewed-build-kit/r9');S=Path('/srv/android/asus-product-integration-staging/r9');F=Path('/srv/android/asus-reviewed-build-kit/r9-fixtures')
for p in [R,S,F]:p.mkdir()
(R/'evidence').mkdir();(R/'scripts').mkdir();(R/'inputs').mkdir()
rels=['.repo/projects/external/chromium-webview/prebuilt/arm64.git','.repo/project-objects/LineageOS/android_external_chromium-webview_prebuilt_arm64.git','external/chromium-webview/prebuilt/arm64/.git','external/chromium-webview/prebuilt/arm64/.gitattributes']
r={}
for rel in rels:
 p=A/rel
 if p.is_file():r[rel]=p.read_text()
 elif p.is_dir():
  r[rel]={n:(p/n).read_text(errors='replace') for n in ['config','HEAD','FETCH_HEAD','packed-refs','archive.json','receipt.json'] if (p/n).is_file()}
  r[rel]['files']=[str(x.relative_to(p)) for x in p.glob('*')]
for url in ['https://api.github.com/repos/LineageOS/android_external_chromium-webview_prebuilt_arm64/commits/main','https://raw.githubusercontent.com/LineageOS/android_external_chromium-webview_prebuilt_arm64/main/webview.apk','https://raw.githubusercontent.com/LineageOS/android_external_chromium-webview_prebuilt_arm64/main/.gitattributes']:
 try:
  with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'exact-r9-artifact-audit'}),timeout=30) as f:
   b=f.read(200000);r[url]=dict(url=f.url,status=f.status,bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),text=b.decode())
 except Exception as e:r[url]=dict(error=str(e))
(R/'evidence/upstream-initial.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
'''
r=remote.run(s);Path('2026-11-06-asus-r9-webview-continuation/evidence/upstream-initial.json').write_text(r);print(r[:16000])
