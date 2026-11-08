from pathlib import Path
import urllib.request,base64,hashlib,json
S=Path(__file__).resolve().parents[1];records=[]
paths=[('platform/system/extras','ext4_utils/ext4_utils.h'),('platform/system/extras','ext4_utils/make_ext4fs.c'),('platform/system/extras','ext4_utils/ext4_utils.c'),('platform/system/core','fs_mgr/fs_mgr.c'),('platform/bootable/recovery','device.cpp'),('platform/bootable/recovery','ui.cpp')]
for repo,path in paths:
 url=f'https://android.googlesource.com/{repo}/+/android-7.0.0_r1/{path}?format=TEXT'
 with urllib.request.urlopen(url,timeout=20) as r:raw=r.read(512*1024)
 assert len(raw)<512*1024;b=base64.b64decode(raw);name='aosp7__'+path.replace('/','_');(S/'inputs'/name).write_bytes(b)
 records.append(dict(url=url,file=name,sha256=hashlib.sha256(b).hexdigest(),bytes=len(b)))
(S/'evidence/reference-pins.json').write_text(json.dumps(records,indent=2)+'\n');print(json.dumps({'fetched':len(records)}))
