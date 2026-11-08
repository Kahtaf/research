from pathlib import Path
import remote,json
s=r'''
from pathlib import Path
import json,urllib.request,urllib.error,base64,hashlib
R=Path('/srv/android/asus-reviewed-build-kit/r9');F=Path('/srv/android/asus-reviewed-build-kit/r9-fixtures/siso-source');rows=[]
for rel in ['siso/build/step_manifest.go']:
 u='https://chromium.googlesource.com/build/+/refs/tags/siso/v1.5.8/'+rel+'?format=TEXT'
 try:
  with urllib.request.urlopen(u,timeout=20) as f:b=base64.b64decode(f.read(2000000));status=f.status
  out=F/rel.replace('/','_');out.write_bytes(b);lines=b.decode().splitlines();selected=set()
  for n,l in enumerate(lines):
   if any(x in l for x in ['edgeHash','EdgeHash','cmdHash','CmdHash']):selected.update(range(max(0,n-3),min(len(lines),n+5)))
  rows.append(dict(url=u,path=str(out),status=status,sha256=hashlib.sha256(b).hexdigest(),matching_context=[dict(line=n+1,text=lines[n]) for n in sorted(selected)]))
 except urllib.error.HTTPError as e:rows.append(dict(url=u,status=e.code))
 except Exception as e:rows.append(dict(url=u,error=str(e)))
with (R/'evidence/siso-step-manifest-semantics.json').open('x') as f:json.dump(rows,f,indent=2);f.write('\n')
print(json.dumps(rows,indent=2))
'''
r=remote.run(s);Path('2026-11-06-asus-r9-webview-continuation/evidence/siso-step-manifest-semantics.json').write_text(r);print(r[:16000])
