from pathlib import Path
import remote,json
s=r'''
from pathlib import Path
import json,urllib.request,urllib.error,base64,hashlib
R=Path('/srv/android/asus-reviewed-build-kit/r9');F=Path('/srv/android/asus-reviewed-build-kit/r9-fixtures/siso-source');F.mkdir();r=[]
urls=[('v158-build','https://chromium.googlesource.com/build/+/refs/tags/siso/v1.5.8/siso/hashfs/proto/state.proto?format=TEXT'),('v158-infra','https://chromium.googlesource.com/infra/infra/+/refs/tags/siso/v1.5.8/go/src/infra/build/siso/hashfs/proto/state.proto?format=TEXT'),('v167-build','https://chromium.googlesource.com/build/+/refs/tags/siso/v1.6.7/siso/hashfs/proto/state.proto?format=TEXT')]
for name,u in urls:
 try:
  with urllib.request.urlopen(u,timeout=20) as f:b=base64.b64decode(f.read(200000));status=f.status
  with (F/(name+'.proto')).open('xb') as out:out.write(b)
  r.append(dict(name=name,url=u,status=status,sha256=hashlib.sha256(b).hexdigest(),text=b.decode()))
 except urllib.error.HTTPError as e:r.append(dict(name=name,url=u,status=e.code))
 except Exception as e:r.append(dict(name=name,url=u,error=str(e)))
with (R/'evidence/siso-schema-routes.json').open('x') as f:json.dump(r,f,indent=2);f.write('\n')
print(json.dumps(r,indent=2))
'''
r=remote.run(s);Path('2026-11-06-asus-r9-webview-continuation/evidence/siso-schema-routes.json').write_text(r);print(r)
