from pathlib import Path
import base64,hashlib,json,sys
from vm import channel
r=Path(__file__).resolve().parents[1]
script=Path(sys.argv[1]).read_text()
# No new TCP connection is permitted if the owned master is absent.
import subprocess
q=subprocess.run(channel()+['python3 -B -'],input=script,text=True,capture_output=True)
(r/'evidence'/(Path(sys.argv[1]).stem+'.stderr')).write_text(q.stderr)
if q.returncode:
 (r/'evidence'/(Path(sys.argv[1]).stem+'.failure')).write_text(q.stdout)
 raise RuntimeError(q.stderr[-3000:])
d=json.loads(q.stdout)
for name,v in d.get('files',{}).items():
 p=r/name;assert r in p.parents
 p.parent.mkdir(parents=True,exist_ok=True)
 b=base64.b64decode(v['data']);assert hashlib.sha256(b).hexdigest()==v['sha256'];p.write_bytes(b)
(r/'evidence'/(Path(sys.argv[1]).stem+'.json')).write_text(json.dumps({k:v for k,v in d.items() if k!='files'},indent=2)+'\n')
print(json.dumps({k:v for k,v in d.items() if k!='files'},indent=2))
