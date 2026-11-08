from remote import SSH
from pathlib import Path
import subprocess,json,hashlib
R=Path(__file__).resolve().parents[1];name='fresh_userdata.reference-1MiB.json';b=subprocess.check_output(SSH+['cat /srv/android/asus-internal-data-validation/evidence/'+name]);j=json.loads(b);m=json.loads((R/'evidence/image-manifest.json').read_text());assert j['bytes']==m['bytes'] and j['sha256']==m['sha256'] and len(j['chunks'])==10807
with (R/'evidence'/name).open('xb') as f:f.write(b)
print(len(b),hashlib.sha256(b).hexdigest())
