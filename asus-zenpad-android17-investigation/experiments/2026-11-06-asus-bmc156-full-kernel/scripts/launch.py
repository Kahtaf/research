from pathlib import Path
import sys,json
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'2026-11-06-asus-product-input-build-kit/scripts'))
from remote import run
L=Path(__file__).resolve().parents[1]
payload={n:(L/'scripts'/n).read_text() for n in ['build.py','verify_full.py','reconstruct.py','resume-reconstruction.py']}
s='''from pathlib import Path
import subprocess,json,shutil
R=Path('/srv/android/asus-bmc156-full-kernel-r1')
assert R.resolve()==R and (R/'evidence/reconstruction.json').is_file()
assert not (R/'evidence/build-status.json').exists() and not (R/'evidence/launch.json').exists()
assert shutil.disk_usage(R).free>30*1024**3
payload=PAYLOAD
for n,s in payload.items():
 p=R/'scripts'/n;assert not p.exists();p.write_text(s)
with (R/'evidence/supervisor.log').open('x') as f:
 p=subprocess.Popen(['python3','-B',str(R/'scripts/build.py')],stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
record=dict(pid=p.pid,script=str(R/'scripts/build.py'),prefix=str(R))
(R/'evidence/launch.json').write_text(json.dumps(record,indent=2)+'\\n')
print(json.dumps(record))
'''.replace('PAYLOAD',repr(payload))
result=run(s);(L/'evidence/launch.stdout').write_text(result);print(result)
