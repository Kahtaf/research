from pathlib import Path
import sys,json
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'2026-11-06-asus-product-input-build-kit/scripts'))
from remote import run
assert len(sys.argv)==2 and sys.argv[1] in ['verify_full','export']
L=Path(__file__).resolve().parents[1];stage=sys.argv[1]
script='''from pathlib import Path
import subprocess,json,shutil,datetime
R=Path('/srv/android/asus-bmc156-full-kernel-r1');E=R/'evidence'
assert R.resolve()==R and E.resolve()==E and shutil.disk_usage(R).free>1024**3
status=json.loads((E/'build-status.json').read_text());assert status['status']=='complete' and status['exit']==0
stage=STAGE
record=E/(stage+'-execution.json');assert not record.exists(),'Existing stage receipt; inspect rather than overwrite'
cmd=['python3','-B',str(R/'scripts'/(stage+'.py'))]
start=datetime.datetime.now(datetime.timezone.utc).isoformat();p=subprocess.run(cmd,capture_output=True,text=True)
r=dict(command=cmd,started=start,finished=datetime.datetime.now(datetime.timezone.utc).isoformat(),exit=p.returncode,stdout=p.stdout,stderr=p.stderr)
record.write_text(json.dumps(r,indent=2)+'\\n');print(json.dumps(r))
'''.replace('STAGE',repr(stage))
s=run(script);(L/'evidence'/(stage+'-remote.stdout')).write_text(s);print(s)
assert json.loads(s)['exit']==0
