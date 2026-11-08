import hashlib,json
from bounded import R,run
T=R/'tools/host';I=R/'inputs';A=R/'artifacts'
# Keep this entire suite inside one command lock. policy_checks has independent
# CPU/wall/observed-memory bounds for each native child and no command-lock import.
q=run(['python3','-B',R/'tests/policy_checks.py'],timeout=190)
print(q.stdout.strip())
q=run([T/'policy_audit',I/'base-policy',A/'UNQUALIFIED-future5role-policy',I/'restore-sepolicy'],timeout=10)
(R/'evidence/final-policy-audit.json').write_text(q.stdout)
p=run([T/'policy_audit',I/'base-policy',I/'restore-sepolicy',I/'restore-sepolicy'],expect=None,timeout=10)
assert p.returncode!=0 and 'Assertion failed' in p.stderr
(R/'evidence/frozen-not-final5role.json').write_text(json.dumps(dict(passed=True,frozen_policy_rejected_as_future=True,returncode=p.returncode,stderr=p.stderr),indent=2)+'\n')
print('FINAL_AUDIT_PASS_AND_FROZEN_REFUSED')
