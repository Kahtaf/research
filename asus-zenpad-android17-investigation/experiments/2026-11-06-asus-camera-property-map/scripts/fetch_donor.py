from pathlib import Path
import urllib.request,json,base64,hashlib
r=Path(__file__).resolve().parents[1]
repo='https://android.googlesource.com/platform/system/core'
u=repo+'/+/android-6.0.1_r1?format=JSON'
d=urllib.request.urlopen(u,timeout=30).read(); (r/'evidence/donor-commit.json').write_bytes(d)
commit=json.loads(d[4:])['commit']
pins=[]
for rel in ['include/utils/PropertyMap.h','libutils/PropertyMap.cpp','NOTICE']:
 url=repo+'/+/'+commit+'/'+rel+'?format=TEXT'
 data=base64.b64decode(urllib.request.urlopen(url,timeout=30).read());p=r/'donor'/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
 pins.append({'repository':repo,'tag':'android-6.0.1_r1','commit':commit,'path':rel,'url':url,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)})
(r/'evidence/donor-pins.json').write_text(json.dumps(pins,indent=2)+'\n')
print(json.dumps(pins,indent=2))
