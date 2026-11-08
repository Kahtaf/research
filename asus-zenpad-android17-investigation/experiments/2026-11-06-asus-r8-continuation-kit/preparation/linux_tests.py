exec(open('2026-11-06-asus-r8-continuation-kit/preparation/inspect_remote.py').read().split('script=r')[0])
r=m.run(r'''
from pathlib import Path
import subprocess,json,os,resource
R=Path('/srv/android/asus-reviewed-build-kit/r8');F=Path('/srv/android/asus-reviewed-build-kit/r8-fixtures/linux-tests-sealed');F.mkdir(parents=True)
p=subprocess.run(['python3','-B',str(R/'scripts/run_tests.py')],capture_output=True,text=True,cwd=R)
(F/'tests.log').write_text(p.stdout+p.stderr)
print(json.dumps(dict(exit=p.returncode,log=p.stdout+p.stderr),indent=2))
''');Path('2026-11-06-asus-r8-continuation-kit/evidence/linux-tests-sealed.json').write_text(r);print(r)
