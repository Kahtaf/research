"""Read-only original snapshots; write review diffs/pins only inside this spike."""
import difflib
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ORIGINAL=ROOT.parent/'2026-11-06-asus-full-install-bounded-host-io'


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def emit(name,value):(ROOT/'evidence'/name).write_text(json.dumps(value,indent=2)+'\n')


before=json.loads((ROOT/'evidence/input-pins.json').read_text())
post=[dict(path=path,before_sha256=pin,after_sha256=digest(ROOT.parent/path),unchanged=pin==digest(ROOT.parent/path)) for path,pin in before.items()]
assert all(row['unchanged'] for row in post),'original implementation/review/boolean fix drift'
emit('prepost-pins.json',post)
code={str(p.relative_to(ROOT)):digest(p) for p in sorted(ROOT.rglob('*.py'))}
emit('code-pins.json',code)
changed=[];runtime=[];verification=[]
for path in sorted((ROOT/'source').rglob('*.py')):
    relative=path.relative_to(ROOT);prior=ORIGINAL/relative
    a=prior.read_text().splitlines(True) if prior.exists() else [];b=path.read_text().splitlines(True)
    if a==b:continue
    diff=list(difflib.unified_diff(a,b,fromfile='a/'+str(relative) if prior.exists() else '/dev/null',tofile='b/'+str(relative)))
    changed.append(dict(path=str(relative),before_sha256=digest(prior) if prior.exists() else None,
                        after_sha256=digest(path),added_lines=sum(x.startswith('+') and not x.startswith('+++') for x in diff),
                        deleted_lines=sum(x.startswith('-') and not x.startswith('---') for x in diff)))
    (verification if path.name=='verify_handoff.py' else runtime).extend(diff)
(ROOT/'evidence/host-lifecycle.patch').write_text(''.join(runtime))
(ROOT/'evidence/verification.patch').write_text(''.join(verification))
emit('changed-code-pins.json',changed)
fix=ROOT.parent/'2026-11-06-asus-install-contract-boolean-fix'
pins=json.loads((fix/'source-pins.json').read_text())
old=(ROOT.parent/pins['original']).read_text()
old_guard="contract['mode']!='PARENT_APPROVED' or not contract['armed']"
new_guard="contract['mode']!='PARENT_APPROVED' or contract['armed'] is not True"
assert old.count(old_guard)==1
strict=old.replace(old_guard,new_guard)
assert hashlib.sha256(old.encode()).hexdigest()==pins['before_sha256']
assert hashlib.sha256(strict.encode()).hexdigest()==pins['after_sha256']
patch=''.join(difflib.unified_diff(old.splitlines(True),strict.splitlines(True),fromfile='a/source/parent_remote.py',tofile='b/source/parent_remote.py'))
assert patch==(fix/'strict-armed.patch').read_text()
assert new_guard in (ROOT/'source/parent_remote.py').read_text()
emit('armed-delta-verification.json',dict(exact_parent_patch_incorporated=True,before_sha256=pins['before_sha256'],strict_only_after_sha256=pins['after_sha256'],guard_only_before_pass=json.loads((ROOT/'evidence/armed-before.json').read_text())['pass'],guard_only_after_pass=json.loads((ROOT/'evidence/armed-after.json').read_text())['pass'],scope='actual guard-only regression; not a full CLI claim'))
print(json.dumps(dict(preserved_input_files=len(post),code_files=len(code),code_pin_manifest_sha256=digest(ROOT/'evidence/code-pins.json'),runtime_diff_lines=len(runtime)),indent=2))
