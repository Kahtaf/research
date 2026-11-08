from pathlib import Path
import sys,json
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R.parent/'2026-11-06-asus-product-input-build-kit/scripts'))
from remote import run
payload={str(p.relative_to(R)):p.read_text() for p in [R/'scripts/build.py',*sorted((R/'source').glob('*'))] if p.is_file()}
payload['source/trace-pins.json']=(R.parent/'2026-11-07-asus-linux49-retained-boot-trace/evidence/patch-check.json').read_text()
script='''from pathlib import Path
import subprocess
R=Path('/srv/android/asus-retained-trace-kernel-probe-20261107')
assert not R.exists(), 'Owned prefix already exists; inspect, never restart blindly'
R.mkdir()
for n in ['scripts','source','evidence','tmp']: (R/n).mkdir()
payload=PAYLOAD
for rel,s in payload.items(): (R/rel).write_text(s)
p=subprocess.run(['python3','-B',str(R/'scripts/build.py')])
raise SystemExit(p.returncode)
'''.replace('PAYLOAD',repr(payload))
print(run(script),flush=True)
