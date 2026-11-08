from pathlib import Path
import sys,json
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R.parent/'2026-11-06-asus-product-input-build-kit/scripts'))
from remote import run
payload=(R/'scripts/prepare.py').read_text()
s='''from pathlib import Path
import subprocess,json
R=Path('/srv/android/asus-early-uart-disabled-kernel-20261107')
assert not R.exists(),'Owned prefix already exists; refuse retry'
R.mkdir()
for n in ['scripts','source','evidence','tmp','artifacts']:(R/n).mkdir()
(R/'scripts/prepare.py').write_text(PAYLOAD)
p=subprocess.run(['python3','-B',str(R/'scripts/prepare.py')],capture_output=True,text=True)
print(p.stdout);print(p.stderr)
'''.replace('PAYLOAD',repr(payload))
print(run(s))
