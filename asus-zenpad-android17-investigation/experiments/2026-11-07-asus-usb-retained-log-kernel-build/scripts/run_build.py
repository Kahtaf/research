from pathlib import Path
import sys,json
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R.parent/'2026-11-06-asus-product-input-build-kit/scripts'))
from remote import run
payload={n:(R/n).read_text() for n in ['scripts/build.py','source/retained-linux-owned-initialization.patch']}
script='''from pathlib import Path
import subprocess,json
R=Path('/srv/android/asus-usb-retained-log-kernel-build-20261107')
assert not R.exists(), 'Owned prefix already exists; refuse retry'
R.mkdir()
for n in ['scripts','source','evidence','tmp','artifacts']:(R/n).mkdir()
for n,s in PAYLOAD.items():(R/n).write_text(s)
with (R/'evidence/build-job.stdout').open('w') as out, (R/'evidence/build-job.stderr').open('w') as err:
 p=subprocess.Popen(['python3','-B',str(R/'scripts/build.py')],stdin=subprocess.DEVNULL,stdout=out,stderr=err,start_new_session=True)
receipt=dict(pid=p.pid,owned_prefix=str(R),supervisor_timeout=None,attempts=1)
(R/'evidence/launch.json').write_text(json.dumps(receipt,indent=2)+'\\n')
print(json.dumps(receipt))
'''.replace('PAYLOAD',repr(payload))
result=run(script)
(R/'evidence/launch.json').write_text(result)
print(result,end='')
