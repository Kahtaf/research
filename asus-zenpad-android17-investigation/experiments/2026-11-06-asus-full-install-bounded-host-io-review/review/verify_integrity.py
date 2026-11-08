"""Read only the explicitly pinned small review inputs; never read image payloads."""
import difflib
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
WORKSPACE=ROOT.parent
SUBJECT=WORKSPACE/'2026-11-06-asus-full-install-bounded-host-io'
UPSTREAM=WORKSPACE/'2026-11-06-asus-rescue-remote-source'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

before=json.loads((ROOT/'evidence/review-input-before.json').read_text())
rows=[dict(path=p,before_sha256=h,after_sha256=digest(WORKSPACE/p)) for p,h in before.items()]
assert all(r['before_sha256']==r['after_sha256'] for r in rows)
inputs=json.loads((ROOT/'evidence/input-pins.json').read_text())
assert all(digest(WORKSPACE/p)==h for p,h in inputs.items())
prepost=json.loads((ROOT/'evidence/prepost-pins.json').read_text())
assert all(r['unchanged'] and r['before_sha256']==r['after_sha256']==inputs[r['path']] for r in prepost)
code=json.loads((ROOT/'evidence/code-pins.json').read_text())
assert all(digest(ROOT/p)==h==digest(SUBJECT/p) for p,h in code.items())
changes=json.loads((ROOT/'evidence/changed-code-pins.json').read_text())
patches=[]
for row in changes:
    rel=row['path'];old=UPSTREAM/rel;new=ROOT/rel
    assert digest(new)==row['after_sha256']
    assert (digest(old) if old.exists() else None)==row['before_sha256']
    oldlines=old.read_text().splitlines(True) if old.exists() else []
    delta=list(difflib.unified_diff(oldlines,new.read_text().splitlines(True),
        fromfile='upstream/'+rel if old.exists() else '/dev/null',tofile='bounded/'+rel))
    assert sum(x.startswith('+') and not x.startswith('+++') for x in delta)==row['added_lines']
    assert sum(x.startswith('-') and not x.startswith('---') for x in delta)==row['deleted_lines']
    patches.extend(delta)
rebuilt=''.join(patches)
assert rebuilt==(ROOT/'evidence/host-io.patch').read_text()
sys.path.insert(0,str(ROOT/'source'))
import verify_handoff
result=verify_handoff.verify()
result.update(input_files_rechecked=len(rows),all_reviewed_and_original_files_unchanged=True,
              prepost_input_pins_consistent=True,changed_code_pins_consistent=True,
              exact_unified_patch_reconstructed=True,source_test_copies_byte_exact=True,
              code_pin_document_sha256=digest(ROOT/'evidence/code-pins.json'))
(ROOT/'evidence/review-input-after.json').write_text(json.dumps(rows,indent=2)+'\n')
(ROOT/'evidence/integrity.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
