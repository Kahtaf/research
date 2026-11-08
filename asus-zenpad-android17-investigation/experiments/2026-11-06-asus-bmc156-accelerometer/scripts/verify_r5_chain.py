from pathlib import Path
import json,hashlib
R=Path('/srv/android/asus-bmc156-accelerometer-r1');B=Path('/srv/android/asus-build-continuation')
snapshot=B/'evidence/snapshot.json';receipt=B/'integration-r5/source-receipt.json'
a=json.loads(snapshot.read_text());b=json.loads(receipt.read_text());ours=json.loads((R/'evidence/baseline-source-hashes.json').read_text())
expected=dict(a['files']);expected.update({p:v['after'] for p,v in b['changes'].items()})
assert ours==expected,{'unexpected':list(set(ours)-set(expected))[:20],'mismatched':[p for p in ours.keys()&expected.keys() if ours[p]!=expected[p]][:20]}
record=dict(exact_parent_compiled_r5_source_match=True,baseline_source_files=len(ours),parent_base_files=len(a['files']),parent_r5_changes=len(b['changes']),parent_base_commit=b['base_commit'],snapshot_sha256=hashlib.sha256(snapshot.read_bytes()).hexdigest(),parent_source_receipt_sha256=hashlib.sha256(receipt.read_bytes()).hexdigest(),parent_full_delta_sha256=b['patch_sha256'])
(R/'evidence/r5-source-chain.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))
