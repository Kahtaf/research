"""Finish cleanup of the retained read-only identity capture after policy review."""
from pathlib import Path
import datetime,fcntl,hashlib,json,subprocess,sys
from preflight import R,W,HELPER,HELPER_SHA,ENDPOINT,FILES
nonce='65dbaa8d29fafca8'
out=R/'inputs'/nonce;remote='/data/local/tmp/asus-framework-identity-'+nonce
assert hashlib.sha256(HELPER.read_bytes()).hexdigest()==HELPER_SHA
accept=json.loads((R/'evidence/parent-policy-acceptance.json').read_text())
assert accept['accepted'] is True
calls=json.loads((R/'evidence'/f'preflight-{nonce}-calls.json').read_text())
assert all(c['exit']==0 for c in calls) and len(calls)==8
pins={}
for name,(path,size,pin) in FILES.items():
 p=out/name;actual=hashlib.sha256(p.read_bytes()).hexdigest()
 expected='6fb632761442cbe7b2d495ddfe9a9da3e4a5063251a9828a2d0f56e6aa95dca2' if name=='policy' else pin
 assert not p.is_symlink() and actual==expected
 if size is not None:assert p.stat().st_size==size
 pins[path]=dict(bytes=p.stat().st_size,sha256=actual)
body=f'''set -eu
if pidof uncrypt; then exit 91; fi
[ ! -e /dev/socket/uncrypt ]
[ "$(getprop init.svc.uncrypt)" != running ]
[ "$(getprop init.svc.setup-bcb)" != running ]
[ "$(getprop init.svc.clear-bcb)" != running ]
[ ! -L {remote} ]
[ "$(stat -c '%u:%g:%a' {remote})" = 0:0:711 ]
'''
for name in FILES:
 body+=f'''[ ! -L {remote}/{name} ]
[ "$(stat -c '%u:%g:%a:%h' {remote}/{name})" = 2000:2000:600:1 ]
'''
body+='rm '+' '.join(remote+'/'+n for n in FILES)+f'\nrmdir {remote}\n'
(R/'evidence/identity-cleanup-intent.json').write_text(json.dumps(dict(body=body),indent=2)+'\n')
with (W/'2026-11-06-asus-recovery-control-transport/evidence/execute.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 p=subprocess.run([sys.executable,str(HELPER)],input=body,text=True,capture_output=True,timeout=95)
 (R/'evidence/identity-cleanup-result.json').write_text(json.dumps(dict(exit=p.returncode,stdout=p.stdout,stderr=p.stderr),indent=2)+'\n')
 assert p.returncode==0
result=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),nonce=nonce,descriptor=next(l.strip() for l in calls[0]['stdout'].splitlines() if 'recovery:' in l),files=pins,live_metadata=calls[1]['stdout'],staging_cleaned=True,api_invoked=False,policy_order_equivalence_accepted=True,policy_acceptance_sha256=hashlib.sha256((R/'evidence/parent-policy-acceptance.json').read_bytes()).hexdigest())
(R/'evidence/live-preflight.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
