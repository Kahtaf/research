from pathlib import Path
import sys,json
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R.parent/'2026-11-06-asus-product-input-build-kit/scripts'))
from remote import run
names=['scripts/build.py','source/early-retained-checkpoint.patch','evidence/next-trace-patch.json']
payload={n:(R/n).read_text() for n in names}
script='''from pathlib import Path
import subprocess
R=Path('/srv/android/asus-early-retained-kernel-probe-20261107')
assert not R.exists(), 'Owned prefix already exists; never restart blindly'
R.mkdir()
for n in ['scripts','source','evidence','tmp','artifacts']:(R/n).mkdir()
for n,s in PAYLOAD.items():(R/n).write_text(s)
p=subprocess.run(['python3','-B',str(R/'scripts/build.py')],capture_output=True,text=True)
(R/'evidence/build-job.stdout').write_text(p.stdout)
(R/'evidence/build-job.stderr').write_text(p.stderr)
print(p.stdout, end='')
print(p.stderr, end='')
print('build_driver_exit='+str(p.returncode))
'''.replace('PAYLOAD',repr(payload))
print(run(script),flush=True)
