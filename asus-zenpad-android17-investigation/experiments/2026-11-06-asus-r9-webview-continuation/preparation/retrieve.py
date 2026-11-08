import remote,json
from pathlib import Path
s=r'''
from pathlib import Path
import json,urllib.request,hashlib,os,datetime
A=Path('/srv/android/lineage24');R=Path('/srv/android/asus-reviewed-build-kit/r9');S=Path('/srv/android/asus-product-integration-staging/r9')
commit='5de662a4d42b57a2efe4114e499d38fa3ce41f9d';repo='LineageOS/android_external_chromium-webview_prebuilt_arm64';oid='1d2f61832b2596b0046cb82cf3634609ea866098d097a83fac27c35272ac726a';size=260835655
pointer=(A/'external/chromium-webview/prebuilt/arm64/webview.apk').read_bytes()
assert hashlib.sha256(pointer).hexdigest()=='a7b12c1895a3b354a91997fffe0e383a88e5b0e0d4371f8fdc090c71f62aade7'
metadata={}
for name in ['webview.apk','.gitattributes']:
 u=f'https://raw.githubusercontent.com/{repo}/{commit}/{name}'
 with urllib.request.urlopen(u,timeout=30) as f:b=f.read(4096);metadata[name]=dict(url=u,status=f.status,sha256=hashlib.sha256(b).hexdigest(),text=b.decode())
 if name=='webview.apk':assert b==pointer
url=f'https://media.githubusercontent.com/media/{repo}/{commit}/webview.apk'
part=S/'webview.apk.part';dst=S/'webview.apk';h=hashlib.sha256();n=0
with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'exact-r9-materialization'}),timeout=60) as f,part.open('xb') as out:
 status=f.status;final_url=f.url;length=f.headers.get('Content-Length')
 assert status==200
 if length:assert int(length)==size
 for b in iter(lambda:f.read(1048576),b''):
  n+=len(b);assert n<=size;h.update(b);out.write(b)
 out.flush();os.fsync(out.fileno())
assert n==size and h.hexdigest()==oid
os.link(part,dst);part.unlink()
receipt=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),repository='https://github.com/'+repo,commit=commit,pointer_sha256=hashlib.sha256(pointer).hexdigest(),oid_sha256=oid,bytes=n,metadata=metadata,download=dict(request_url=url,final_url=final_url,status=status,content_length=length,streaming_verified=True),payload_path=str(dst),active_source_changed=False)
with (R/'evidence/retrieval.json').open('x') as f:json.dump(receipt,f,indent=2);f.write('\n')
print(json.dumps(receipt,indent=2))
'''
r=remote.run(s);Path('2026-11-06-asus-r9-webview-continuation/evidence/retrieval.json').write_text(r);print(r)
