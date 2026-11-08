"""Verify the one-file runtime correction and preserved public inputs offline."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT.parent
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

pins = json.loads((ROOT / 'evidence/input-pins.json').read_text())
for original, row in pins.items():
    assert sha(WORK / original) == row['sha256'], original
old = WORK / '2026-11-06-asus-full-install-host-lifecycle-fix'
changes = []
for source in sorted((old / 'source').rglob('*.py')):
    relative = source.relative_to(old)
    if sha(source) != sha(ROOT / relative):
        changes.append(str(relative))
assert changes == ['source/source_client.py'], changes
for relative, expected in json.loads((ROOT / 'evidence/code-pins.json').read_text()).items():
    assert sha(ROOT / relative) == expected, relative
for name, count in [('qa.json', 46), ('regression-results.json', 45), ('focused-results.json', 14)]:
    report = json.loads((ROOT / 'evidence' / name).read_text())
    assert report['tests'] == count and report['failures'] == report['errors'] == 0
    assert report['all_children_reaped']
print(json.dumps(dict(preserved_inputs=len(pins), sole_runtime_delta=changes,
                     inherited_flow_cases=105, all_final_children_reaped=True,
                     device_or_network_contacted=False, deployment_approved=False)))
