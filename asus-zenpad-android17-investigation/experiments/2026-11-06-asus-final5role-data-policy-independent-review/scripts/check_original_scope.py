"""Run original suite with only fixture paths/output and execution limits adapted;
compare every original command, status and stdout against the expanded suite.
"""
from bounded import R,run
import json,hashlib
p=R/'baseline/tests/policy_checks.py';s=p.read_text()
adapted=s.replace("A=R/'artifacts';T=Path('/srv/android/asus-target-rescue/artifacts/tools-delivery')","A=R/'inputs';T=R/'tools/host'")
adapted=adapted.replace("A/'restore-sepolicy'","R/'inputs/reviewed-policy'")
adapted=adapted.replace('checks=[]',"import resource\ndef limits():\n resource.setrlimit(resource.RLIMIT_CPU,(10,10))\n resource.setrlimit(resource.RLIMIT_CORE,(0,0))\nchecks=[]",1)
adapted=adapted.replace('capture_output=True,text=True)','capture_output=True,text=True,timeout=10,preexec_fn=limits)')
adapted=adapted.replace("R/'evidence/policy-checks.json'","R/'evidence/original-scope-checks.json'")
target=R/'tests/original_scope_adapted.py';target.write_text(adapted)
run(['python3','-B',target],timeout=60)
old=json.loads((R/'evidence/original-scope-checks.json').read_text());new=json.loads((R/'evidence/policy-checks.json').read_text())
def norm(row):
 command=row['command'];return dict(tool=__import__('pathlib').Path(command[0]).name,args=['<binary-policy-or-contexts>',*command[2:]],returncode=row['returncode'],stdout=row['stdout'],passed=row['passed'])
a=list(map(norm,old['checks']));b=list(map(norm,new['checks']));assert len(a)==72 and len(b)==218
assert a[:43]==b[:43] and a[43:]==b[-29:]
assert old['compiled_rows']==new['compiled_rows']==907 and old['compiled_context_lookups']==new['compiled_context_lookups']==29
(R/'evidence/original-scope-comparison.json').write_text(json.dumps(dict(passed=True,baseline_source_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),original_checks=72,original_policy_commands=43,original_context_lookups=29,expanded_checks=218,all_original_commands_status_stdout_retained=True,compiled_context_rows=907,adaptation='Only local paths, receipt output and CPU/wall/core limits. Pristine original retained in baseline/.',normalized_original_commands=a),indent=2)+'\n')
print('ORIGINAL_SCOPE_PASS 72/72 commands/status/stdout retained; 29 native lookups')
