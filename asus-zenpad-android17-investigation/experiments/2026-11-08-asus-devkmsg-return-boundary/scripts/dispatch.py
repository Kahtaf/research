from pathlib import Path
import base64,json,subprocess
from vm import R,channel
I=json.loads((R/'evidence/identity.json').read_text())
paths=[R/'scripts/build_remote.py',R/'evidence/identity.json',R/'evidence/prepost.json']+[R/'source'/n for n in json.loads((R/'evidence/prepost.json').read_text())]
files={str(p.relative_to(R)):base64.b64encode(p.read_bytes()).decode() for p in paths}
script='''from pathlib import Path
import base64,json,subprocess,sys
R=Path(DEST);assert not R.exists(),'One dispatch only';R.mkdir()
for n in ['tmp','source','scripts','evidence','artifacts']:(R/n).mkdir()
for n,d in FILES.items():
 p=R/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(base64.b64decode(d))
sys.exit(subprocess.call(['python3','-B',str(R/'scripts/build_remote.py')]))
'''.replace('DEST',repr(I['remote_root'])).replace('FILES',repr(files))
with (R/'evidence/dispatch.json').open('x') as f:json.dump(dict(remote_root=I['remote_root'],one_dispatch=True),f)
p=subprocess.run(channel()+['python3 -B -'],input=script,text=True,capture_output=True)
(R/'evidence/dispatch.stdout').write_text(p.stdout);(R/'evidence/dispatch.stderr').write_text(p.stderr);print(p.stdout);print(p.stderr);p.check_returncode()
