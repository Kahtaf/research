import remote,json
from pathlib import Path
s=r'''
from pathlib import Path
import json,urllib.request,urllib.error,hashlib,os,datetime
R=Path('/srv/android/asus-reviewed-build-kit/r9');S=Path('/srv/android/asus-product-integration-staging/r9')
repo='LineageOS/android_external_chromium-webview_prebuilt_arm64';oid='1d2f61832b2596b0046cb82cf3634609ea866098d097a83fac27c35272ac726a';size=260835655
url=f'https://review.lineageos.org/{repo}.git/info/lfs/objects/batch'
data=json.dumps(dict(operation='download',transfers=['basic'],objects=[dict(oid=oid,size=size)],ref=dict(name='refs/heads/main'))).encode()
r=dict(request_url=url,request=json.loads(data),attempts=[dict(url=f'https://media.githubusercontent.com/media/{repo}/5de662a4d42b57a2efe4114e499d38fa3ce41f9d/webview.apk',status=404)])
try:
 with urllib.request.urlopen(urllib.request.Request(url,data=data,headers={'Accept':'application/vnd.git-lfs+json','Content-Type':'application/vnd.git-lfs+json','User-Agent':'git-lfs/3.7.1'}),timeout=30) as f:
  b=f.read(100000);r['batch']=json.loads(b);r['batch_status']=f.status
 obj=r['batch']['objects'][0];assert obj['oid']==oid and obj['size']==size
 if 'error' not in obj:
  action=obj['actions']['download'];u=action['href'];assert u.startswith('https://')
  part=S/'webview.apk.part';h=hashlib.sha256();n=0
  with urllib.request.urlopen(urllib.request.Request(u,headers=action.get('header',{})),timeout=60) as f,part.open('xb') as out:
   r['payload_status']=f.status
   for b in iter(lambda:f.read(1048576),b''):n+=len(b);assert n<=size;h.update(b);out.write(b)
   out.flush();os.fsync(out.fileno())
  assert n==size and h.hexdigest()==oid
  os.link(part,S/'webview.apk');part.unlink();r.update(bytes=n,sha256=h.hexdigest(),streaming_verified=True)
except urllib.error.HTTPError as e:r['error']=dict(status=e.code,body=e.read(10000).decode(errors='replace'))
except Exception as e:r['error']=str(e)
# Do not export signed URLs or public temporary access headers.
if 'batch' in r:
 for obj in r['batch'].get('objects',[]):
  if 'actions' in obj:obj['actions']={k:{'url_host':urllib.parse.urlparse(v['href']).hostname} for k,v in obj['actions'].items()}
with (R/'evidence/lineage-lfs-batch.json').open('x') as f:json.dump(r,f,indent=2);f.write('\n')
print(json.dumps(r,indent=2))
'''
r=remote.run(s);Path('2026-11-06-asus-r9-webview-continuation/evidence/lineage-lfs-batch.json').write_text(r);print(r)
