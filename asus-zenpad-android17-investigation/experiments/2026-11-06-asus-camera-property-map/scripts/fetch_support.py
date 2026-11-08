from pathlib import Path
import urllib.request,json,base64,hashlib
r=Path(__file__).resolve().parents[1];pins=[]
repo='https://android.googlesource.com/platform/system/core';commit=json.loads((r/'evidence/donor-commit.json').read_bytes()[4:])['commit']
rels=['include/utils/'+x+'.h' for x in ['String8','VectorImpl','SortedVector','KeyedVector','TypeHelpers','SharedBuffer','Vector']]+['libutils/'+x+'.cpp' for x in ['String8','VectorImpl','SharedBuffer','Unicode']]
for rel in rels:
 url=f'{repo}/+/{commit}/{rel}?format=TEXT';data=base64.b64decode(urllib.request.urlopen(url,timeout=30).read());p=r/'donor'/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data);pins.append({'commit':commit,'url':url,'path':rel,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)})
repo='https://android.googlesource.com/platform/system/core'
d=urllib.request.urlopen(repo+'/+/refs/heads/main?format=JSON',timeout=30).read();(r/'evidence/backend-commit.json').write_bytes(d);commit=json.loads(d[4:])['commit']
for rel in ['VectorImpl.cpp','String8.cpp','SharedBuffer.cpp','SharedBuffer.h','Unicode.cpp','include/utils/VectorImpl.h','include/utils/String8.h','include/utils/SortedVector.h','include/utils/KeyedVector.h','include/utils/TypeHelpers.h']:
 upstream='libutils/binder/'+rel if not rel.startswith('include/') else 'libutils/binder/'+rel
 url=f'{repo}/+/{commit}/{upstream}?format=TEXT'
 try:data=base64.b64decode(urllib.request.urlopen(url,timeout=30).read())
 except Exception as e: print('FETCH_FAILED',url,str(e));continue
 p=r/'backend'/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data);pins.append({'commit':commit,'url':url,'path':'backend/'+rel,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)})
(r/'evidence/support-pins.json').write_text(json.dumps(pins,indent=2)+'\n');print(json.dumps(pins,indent=2))
