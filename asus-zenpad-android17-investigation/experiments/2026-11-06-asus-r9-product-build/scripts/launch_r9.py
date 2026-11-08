"""Parent one-shot R9 executor; no retry and no direct native-engine invocation."""
from pathlib import Path
import datetime
import hashlib
import importlib.util
import json

ROOT=Path(__file__).resolve().parents[1]
WORKSPACE=ROOT.parent
KIT_SEAL='744fa117bba0e4ba9895af792ddc71f1cbe99196cb752593e560064ef8d41e69'
REVIEW_SHA='75e0b189a7c66f2a4efd20705266851405231e27550d3b057b1ba335b537187e'
plan=json.loads((ROOT/'evidence/parent-plan-only.json').read_text())
assert plan['exit']==0 and json.loads(plan['stdout'])['kit_pins_sha256']==KIT_SEAL
assert hashlib.sha256((ROOT/'evidence/r8-failure-acceptance.json').read_bytes()).hexdigest()==REVIEW_SHA
with (ROOT/'evidence/launch-intent.json').open('x') as f:
    json.dump({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'kit_seal':KIT_SEAL,
               'review_sha256':REVIEW_SHA,'operation':'PARENT_EXECUTE exactly once','retry':False},f,indent=2)
spec=importlib.util.spec_from_file_location('r9_parent_remote',WORKSPACE/'2026-11-06-asus-product-input-build-kit/scripts/remote.py')
remote=importlib.util.module_from_spec(spec);spec.loader.exec_module(remote)
script="""from pathlib import Path
import subprocess,sys,json,hashlib
root=Path('/srv/android/asus-reviewed-build-kit/r9-exec-r1')
sys.path.insert(0,str(root/'scripts'))
from integrate import verify_pins
assert verify_pins(root)=='744fa117bba0e4ba9895af792ddc71f1cbe99196cb752593e560064ef8d41e69'
review=root/'parent-review/r8-failure-acceptance.json'
assert hashlib.sha256(review.read_bytes()).hexdigest()=='75e0b189a7c66f2a4efd20705266851405231e27550d3b057b1ba335b537187e'
result=subprocess.run([sys.executable,'-B',str(root/'scripts/integrate.py'),'--mode','PARENT_EXECUTE','--prior-failure-review',str(review),'--prior-failure-review-sha256','75e0b189a7c66f2a4efd20705266851405231e27550d3b057b1ba335b537187e'],capture_output=True,text=True)
print(json.dumps({'exit':result.returncode,'stdout':result.stdout,'stderr':result.stderr}))
"""
output=remote.run(script)
result=json.loads(output)
with (ROOT/'evidence/live-executor-return.json').open('x') as f:json.dump(result,f,indent=2)
print(json.dumps(result,indent=2),flush=True)
