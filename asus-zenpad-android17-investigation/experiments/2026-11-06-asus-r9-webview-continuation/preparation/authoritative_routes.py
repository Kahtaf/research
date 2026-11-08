import remote,json
from pathlib import Path
s=r'''
from pathlib import Path
import urllib.request,urllib.error,json,hashlib
R=Path('/srv/android/asus-reviewed-build-kit/r9');repo='LineageOS/android_external_chromium-webview_prebuilt_arm64';c='5de662a4d42b57a2efe4114e499d38fa3ce41f9d';r={}
urls=[f'https://raw.githubusercontent.com/{repo}/{c}/.lfsconfig',f'https://api.github.com/repos/{repo}/git/trees/{c}',f'https://media.githubusercontent.com/media/{repo}/main/webview.apk',f'https://github.com/{repo}/raw/{c}/webview.apk',f'https://api.github.com/repos/{repo}/releases?per_page=3']
for url in urls:
 try:
  with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'exact-pinned-object-audit'}),timeout=30) as f:
   b=f.read(20000);r[url]=dict(status=f.status,final_url=f.url,bytes_read=len(b),sha256=hashlib.sha256(b).hexdigest(),text=b.decode(errors='replace'))
 except urllib.error.HTTPError as e:r[url]=dict(status=e.code,body=e.read(2000).decode(errors='replace'))
 except Exception as e:r[url]=dict(error=str(e))
with (R/'evidence/authoritative-routes.json').open('x') as f:json.dump(r,f,indent=2);f.write('\n')
print(json.dumps(r,indent=2))
'''
r=remote.run(s);Path('2026-11-06-asus-r9-webview-continuation/evidence/authoritative-routes.json').write_text(r);print(r)
