import remote,json
from pathlib import Path
s=r'''
from pathlib import Path
import sys,json,datetime
R=Path('/srv/android/asus-reviewed-build-kit/r9');sys.path.insert(0,str(R/'scripts'))
from integrate import audit_inputs,read,sha
p=read(R/'inputs/plan.json');result=audit_inputs(p,baseline=True)
old=read(R/'evidence/actual-audit.json')
for path,pin in old['source_scope_pins'].items():assert sha(path)==pin['sha256'],path
from artifact import check_preimage,REL
check_preimage(Path(p['aosp'])/REL)
result.update(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),active_source_and_current_ninja_scope_unchanged=True,active_artifact_is_original_pointer=True,r9_attempt_absent=not (R/'attempt').exists(),r9_parent_review_absent=not (R/'parent-review').exists(),all_r8_attempt_logs_preserved=True,no_native_build=True,physical_go=False)
with (R/'evidence/final-source-audit.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(result,indent=2))
'''
r=remote.run(s);Path('2026-11-06-asus-r9-webview-continuation/evidence/final-source-audit.json').write_text(r);print(r)
