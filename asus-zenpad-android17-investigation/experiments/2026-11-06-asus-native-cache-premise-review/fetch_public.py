from pathlib import Path
import urllib.request,base64,json,hashlib
root=Path('2026-11-06-asus-native-cache-premise-review/evidence/public-source');root.mkdir(exist_ok=True)
rev='342ffcda73fb0acb5666792b95c00efc32b47318'
files=['siso/toolsupport/ninjautil/ninja_log.go','siso/subcmd/ninja/ninja.go','siso/build/ninjabuild/deps_log.go','siso/hashfs/state.proto','siso/hashfs/hashfs.go','siso/hashfs/state.go','siso/build/ninjabuild/step.go']
rows=[]
for f in files:
 url=f'https://chromium.googlesource.com/build/+/{rev}/{f}?format=TEXT'
 try:
  data=base64.b64decode(urllib.request.urlopen(url,timeout=20).read(2**22));dest=root/f.replace('/','__');dest.write_bytes(data);rows.append(dict(path=f,url=url,sha256=hashlib.sha256(data).hexdigest(),bytes=len(data)))
 except Exception as e:rows.append(dict(path=f,error=str(e)))
(root/'index.json').write_text(json.dumps(rows,indent=2))
print(json.dumps(rows,indent=2))
