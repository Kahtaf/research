"""Local, read-only delivery verification; no subprocess, network or device IO."""
from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[1]
sha=lambda b:hashlib.sha256(b).hexdigest()
for inventory in ['SOURCE_PINS.json','ARTIFACTS.json']:
 data=json.loads((R/inventory).read_text())
 for name,pin in data['files'].items():
  p=R/name
  assert p.is_file() and not p.is_symlink(),name
  raw=p.read_bytes();assert len(raw)==pin['bytes'] and sha(raw)==pin['sha256'],name
for name,count in [('core-tests.json',24),('host-tests.json',16),('host-durability.json',5)]:
 rows=json.loads((R/'evidence'/name).read_text());assert len(rows)==count and all(r.get('passed',r.get('pass')) for r in rows),name
for name in ['policy-structure.json','policy-checks.json','concat-guest.json','independent-container.json','reproduction.json']:
 assert json.loads((R/'evidence'/name).read_text())['passed'],name
contract=json.loads((R/'artifacts/candidate/session-contract.UNAPPROVED.json').read_text())
assert contract['armed'] is False and contract['execute_approved'] is False and contract['manifest_records']==0
assert (R/'artifacts/unarmed.manifest').read_bytes()[12:16]==bytes(4)
assert 'ARMED = False' in (R/'source/generated_host_binding.py').read_text()
assert contract['p10_full_sha256'] in (R/'source/generated_host_binding.py').read_text()
assert contract['p10_full_sha256']!='cb30e1dd1faf0016bca0a875a80757798993651b19e8c5213626edeece93556b'
assert sha((R/'artifacts/original-recovery.payload').read_bytes())=='902b2f06a01cca574b4aa374e67c4e7f8f0ed53f6e6a55017b6d96351f0f1f20'
logs=json.loads((R/'evidence/build-log.json').read_text());assert all(x['returncode']==0 for x in logs)
legacy=[x for x in logs if 'tests/test_adapters.py' in x['command']];assert len(legacy)==1 and 'Ran 24 tests' in legacy[0]['stderr'] and '\nOK\n' in legacy[0]['stderr']
print(json.dumps(dict(passed=True,unarmed=True,physical_validation=False,source_files=len(json.loads((R/'SOURCE_PINS.json').read_text())['files']),artifact_and_evidence_files=len(json.loads((R/'ARTIFACTS.json').read_text())['files']),p10_full_sha256=contract['p10_full_sha256']),indent=2))
