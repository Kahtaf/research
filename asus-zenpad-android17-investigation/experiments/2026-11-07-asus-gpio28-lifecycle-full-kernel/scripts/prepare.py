from transport import run,L,R
import json
payload={str(p.relative_to(L)):p.read_text() for d in ['scripts','patches','evidence'] for p in (L/d).iterdir() if p.suffix in ['.py','.patch','.json']}
payload['evidence/baseline-toolchains.json']=(L.parent/'2026-11-06-asus-bmc156-full-kernel/evidence/toolchains.json').read_text()
s='''from pathlib import Path
import json,subprocess
R=Path(PREFIX)
assert not R.exists(),'Owned prefix already exists; inspect, never overwrite'
R.mkdir()
for d in ['scripts','patches','evidence']:(R/d).mkdir()
for n,s in PAYLOAD.items():(R/n).write_text(s)
p=subprocess.run(['python3','-B',str(R/'scripts/prepare_remote.py')],text=True,capture_output=True)
(R/'evidence/prepare.stdout').write_text(p.stdout)
(R/'evidence/prepare.stderr').write_text(p.stderr)
print(json.dumps({'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}))
'''.replace('PREFIX',repr(R)).replace('PAYLOAD',repr(payload))
result=run(s);(L/'evidence/preparation-transport.json').write_text(result);print(result)
