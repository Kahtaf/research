from pathlib import Path
import json,base64,hashlib,subprocess,os
from vm import R,channel
os.chdir(R)
q=subprocess.run(channel()+['python3 -B -'],input=(R/'scripts/inspect_remote.py').read_bytes(),capture_output=True)
(R/'evidence/inspect.stderr').write_bytes(q.stderr);q.check_returncode();d=json.loads(q.stdout)
i=json.loads((R/'evidence/identity.json').read_text());assert d['source_link']==i['base_remote_root']+'/kernel' and d['config_sha256']==i['config_sha256'] and d['image_sha256']==i['base_compiled_sha256']
f=d.pop('files');pins={}
for n,v in f.items():
 b=base64.b64decode(v['data']);assert hashlib.sha256(b).hexdigest()==v['sha256'];p=R/'source/base'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b);pins[n]=v['sha256']
d['source_pins']=pins
dis=d.pop('disassembly'); (R/'evidence/base-callflow.disasm').write_text('\n'.join(dis.values())); (R/'evidence/base-delay.disasm').write_text('\n'.join(v for n,v in dis.items() if n in ['__delay','__const_udelay','__udelay','__ndelay'])); (R/'evidence/base-disassembly.json').write_text(json.dumps(dis,indent=2)+'\n')
(R/'evidence/actual-base.json').write_text(json.dumps(d,indent=2)+'\n')
print(json.dumps({k:v for k,v in d.items() if k not in ['source_pins','symbols']},indent=2))
