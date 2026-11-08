from pathlib import Path
import sys,subprocess,json,base64,hashlib
from vm import R,channel
name=sys.argv[1]
s=(R/'scripts'/(name+'.remote.py')).read_text()
p=subprocess.run(channel()+['python3 -B -'],input=s,text=True,capture_output=True,timeout=90)
(R/'evidence'/(name+'.stderr')).write_text(p.stderr)
p.check_returncode()
d=json.loads(p.stdout)
for n,v in d.pop('files',{}).items():
 b=base64.b64decode(v); dest=R/n if n.startswith('evidence/') else R/'source'/n
 dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(b)
 d.setdefault('fetched_files',{})[n]=dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
(R/'evidence'/(name+'.json')).write_text(json.dumps(d,indent=2)+'\n')
print(json.dumps(dict(saved=name,files=len(d.get('fetched_files',{})),metadata_keys=list(d))))
