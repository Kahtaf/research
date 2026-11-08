from pathlib import Path
import urllib.request,base64,hashlib,json
S=Path(__file__).resolve().parents[1];records=[]
for repo,file in [('platform/art','runtime/oat_file.cc'),('platform/external/selinux','libselinux/src/label_file.c')]:
 url=f'https://android.googlesource.com/{repo}/+/android-7.0.0_r1/{file}?format=TEXT'
 with urllib.request.urlopen(url,timeout=20) as r:encoded=r.read(512*1024)
 assert len(encoded)<512*1024;b=base64.b64decode(encoded);dst='source/reference-'+file.replace('/','_');(S/dst).write_bytes(b)
 records.append(dict(file=dst,url=url,bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),role='Format interpretation only; OEM data determines results'))
(S/'evidence/format-references.json').write_text(json.dumps(records,indent=2)+'\n')
