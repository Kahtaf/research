from pathlib import Path
import sys,subprocess,json,datetime
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R.parent/'2026-11-06-asus-product-input-build-kit/scripts'))
from remote import SSH
assert len(sys.argv)==3
script=Path(sys.argv[1]);name=sys.argv[2]
log=R/'evidence'/(name+'.json')
assert not log.exists()
start=datetime.datetime.now(datetime.timezone.utc).isoformat()
try:
    p=subprocess.run(SSH+['python3 -B -'],input=script.read_text(),capture_output=True,text=True,timeout=600)
    row=dict(script=str(script),started=start,exit=p.returncode,stdout=p.stdout,stderr=p.stderr)
except subprocess.TimeoutExpired as e:
    row=dict(script=str(script),started=start,exit='SSH_TIMEOUT',stdout=str(e.stdout),stderr=str(e.stderr))
log.write_text(json.dumps(row,indent=2)+'\n')
print(json.dumps(row,indent=2))
assert row['exit']==0
