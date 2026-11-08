import base64,sys
from remote import R,REMOTE,call
code='''from pathlib import Path
import base64,os,resource,subprocess
r=Path(REMOTE);os.chdir(r);os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
for name in ['concat-guest.json','concat-guest.log']:
 (r/'evidence'/name).rename(r/'evidence'/('first-'+name))
(r/'tests/concat_test.py').write_bytes(base64.b64decode(SOURCE))
p=subprocess.run(['python3','-B','tests/concat_test.py'],capture_output=True,timeout=40)
(r/'evidence/concat-retry.stdout').write_bytes(p.stdout);(r/'evidence/concat-retry.stderr').write_bytes(p.stderr)
print(p.stdout.decode());print(p.stderr.decode());raise SystemExit(p.returncode)
'''.replace('REMOTE',repr(REMOTE)).replace('SOURCE',repr(base64.b64encode((R/'tests/concat_test.py').read_bytes()).decode()))
p=call(code,timeout=60);print(p.stdout.decode());sys.exit(p.returncode)
