from transport import run,L,R
s='''from pathlib import Path
import json,subprocess
R=Path(PREFIX)
assert (R/'evidence/preparation.json').is_file()
assert not (R/'evidence/launch.json').exists() and not (R/'evidence/build-status.json').exists()
with (R/'evidence/supervisor.log').open('x') as f:
 p=subprocess.Popen(['python3','-B',str(R/'scripts/build_remote.py')],stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
r={'pid':p.pid,'prefix':str(R),'script':str(R/'scripts/build_remote.py')}
(R/'evidence/launch.json').write_text(json.dumps(r,indent=2)+'\\n')
print(json.dumps(r))
'''.replace('PREFIX',repr(R))
r=run(s);(L/'evidence/launch.json').write_text(r);print(r)
