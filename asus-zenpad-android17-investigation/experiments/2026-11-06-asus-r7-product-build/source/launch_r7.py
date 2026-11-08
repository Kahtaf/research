"""Persist the one-shot kit supervisor across SSH loss; never retry a launch.
The kit itself owns the original flock continuously and supervises its native
foreground build. This wrapper neither bypasses nor waits for that lock.
"""
from pathlib import Path
import argparse,base64,hashlib,importlib.util,json
R=Path(__file__).resolve().parents[1]
K=R.parent/'2026-11-06-asus-r7-continuation-kit'
SEAL='9287a07d243a9d70abefa0102de160d88af712a574c7fab6032ce9b36920f617'
REMOTE='/srv/android/asus-r7-product-build'
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--execute',action='store_true');a=p.parse_args()
 if not a.execute:
  print(json.dumps(dict(mode='PLAN_ONLY',kit_seal=SEAL,revision='r7',device_contacted=False)));return
 plan=json.loads((R/'evidence/reviewed-plan-preflight.json').read_text())
 assert plan['exit']==0 and json.loads(plan['stdout'])['result']['eligible_at_check_time_only'] is True
 digest=hashlib.sha256((R/'evidence/r6-failure-review.json').read_bytes()).hexdigest()
 assert digest==plan['review_sha256']
 assert hashlib.sha256((K/'inputs/kit-pins.json').read_bytes()).hexdigest()==SEAL
 spec=importlib.util.spec_from_file_location('r7_remote',K/'scripts/remote.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 code=r'''
from pathlib import Path
import datetime,hashlib,json,os,subprocess
R=Path(REMOTE);K=Path('/srv/android/asus-reviewed-build-kit/r7')
assert hashlib.sha256((K/'inputs/kit-pins.json').read_bytes()).hexdigest()==SEAL
review=K/'parent-review/r6-failure.json'
assert hashlib.sha256(review.read_bytes()).hexdigest()==REVIEW
R.mkdir()
argv=['python3','-B',str(K/'scripts/integrate.py'),'--mode','PARENT_EXECUTE','--prior-failure-review',str(review),'--prior-failure-review-sha256',REVIEW]
intent=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),argv=argv,kit_seal=SEAL,review_sha256=REVIEW,no_retry=True)
with (R/'intent.json').open('x') as f:
 json.dump(intent,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
with (R/'supervisor.log').open('xb') as log:
 child=subprocess.Popen(argv,cwd=K,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,close_fds=True,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
result=dict(intent,supervisor_pid=child.pid,prefix=str(R))
with (R/'launch.json').open('x') as f:
 json.dump(result,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
print(json.dumps(result))
'''.replace('REMOTE',repr(REMOTE)).replace('SEAL',repr(SEAL)).replace('REVIEW',repr(digest))
 result=json.loads(m.run(code))
 with (R/'evidence/launch.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
 print(json.dumps(result,indent=2))
if __name__=='__main__':main()
