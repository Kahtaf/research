from pathlib import Path
import sys,json,base64
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R.parent/'2026-11-06-asus-product-input-build-kit/scripts'))
from remote import run
files={}
for n in ['asus_entry_text.S','asus_entry_expected.inc','asus_entry_tag.h']:
 files['kernel/arch/arm64/kernel/'+n]=(R/'source'/n).read_bytes()
for n in ['arch/arm64/kernel/head.S','arch/arm64/kernel/asus_retained_trace.c']:
 files['kernel/'+n]=(R/'source/final'/n).read_bytes()
files['scripts/build.py']=(R/'scripts/build.py').read_bytes()
files['source/expected-runtime.dtb']=(R/'source/expected-runtime.dtb').read_bytes()
files['source/identity.json']=(R/'evidence/identity.json').read_bytes()
payload={n:base64.b64encode(d).decode() for n,d in files.items()}
script='''from pathlib import Path
import json,base64,subprocess,hashlib
R=Path('/srv/android/asus-linux49-entry-text-checkpoint-20261107')
assert not (R/'scripts/build.py').exists()
files=PAYLOAD
for n,encoded in files.items():
 p=R/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(base64.b64decode(encoded))
with (R/'evidence/build-job.stdout').open('w') as out,(R/'evidence/build-job.stderr').open('w') as err:
 p=subprocess.Popen(['python3','-B',str(R/'scripts/build.py')],stdout=out,stderr=err,start_new_session=True)
receipt=dict(pid=p.pid,uploaded={n:hashlib.sha256((R/n).read_bytes()).hexdigest() for n in files},no_build_wall_deadline=True)
(R/'evidence/build-launch.json').write_text(json.dumps(receipt,indent=2)+'\\n')
print(json.dumps(receipt))
'''.replace('PAYLOAD',repr(payload))
result=run(script);(R/'evidence/build-launch.json').write_text(result);print(result)
