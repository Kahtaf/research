from pathlib import Path
import base64,json,subprocess
from vm import R,channel
I=json.loads((R/'evidence/identity.json').read_text());dest=I['remote_root']
files={str(p.relative_to(R)):base64.b64encode(p.read_bytes()).decode() for p in [R/'source/init.c',R/'source/bootformat.py',R/'source/arch/arm64/kernel/asus_entry_tag.h',R/'source/arch/arm64/kernel/asus_retained_trace.c',R/'scripts/build_remote.py',R/'evidence/prepost.json',R/'evidence/identity.json']}
script='''from pathlib import Path
import base64,json,subprocess,sys
R=Path(DEST);assert not R.exists(),'One dispatch only';R.mkdir()
for n in ['tmp','source','scripts','evidence','artifacts']:(R/n).mkdir()
for n,d in FILES.items():
 p=R/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(base64.b64decode(d))
sys.exit(subprocess.call(['python3','-B',str(R/'scripts/build_remote.py')]))
'''.replace('DEST',repr(dest)).replace('FILES',repr(files))
assert not (R/'evidence/dispatch.json').exists();(R/'evidence/dispatch.json').write_text(json.dumps(dict(remote_root=dest,one_dispatch=True)))
p=subprocess.run(channel()+['python3 -B -'],input=script,text=True,capture_output=True)
(R/'evidence/dispatch.stdout').write_text(p.stdout);(R/'evidence/dispatch.stderr').write_text(p.stderr);print(p.stdout);print(p.stderr);p.check_returncode()
