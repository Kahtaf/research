from pathlib import Path
import sys
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R.parent/'2026-11-06-asus-product-input-build-kit/scripts'))
from remote import run
payload=(R/'scripts/build.py').read_text()
s='''from pathlib import Path
import subprocess
R=Path('/srv/android/asus-early-uart-disabled-kernel-20261107')
assert not (R/'scripts/build.py').exists() and not (R/'evidence/build-status.json').exists(),'Existing owned compile refused'
(R/'scripts/build.py').write_text(PAYLOAD)
with (R/'evidence/build-job.stdout').open('w') as out,(R/'evidence/build-job.stderr').open('w') as err:
 p=subprocess.run(['python3','-B',str(R/'scripts/build.py')],stdout=out,stderr=err)
print((R/'evidence/build-job.stdout').read_text());print((R/'evidence/build-job.stderr').read_text());print('build_script_exit='+str(p.returncode))
'''.replace('PAYLOAD',repr(payload))
result=run(s);(R/'evidence/build-run-output.txt').write_text(result);print(result)
