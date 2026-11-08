import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];W=ROOT.parent;H=lambda b:hashlib.sha256(b).hexdigest()
pins=json.loads((ROOT/'evidence/input-pins.json').read_text())
for p in pins:
 assert H((W/p['original']).read_bytes())==p['sha256'],p['original']
 assert H((ROOT/p['copy']).read_bytes())==p['sha256'],p['copy']
changes=json.loads((ROOT/'evidence/pre-post-pins.json').read_text())
for r in changes:
 assert H((ROOT/'candidate'/r['path']).read_bytes())==r['post_sha256']
 assert H((ROOT/'evidence/patch-replay'/r['path']).read_bytes())==r['post_sha256']
 if r['pre_sha256']:assert H((ROOT/'preimage'/r['path']).read_bytes())==r['pre_sha256']
 else:assert not (ROOT/'preimage'/r['path']).exists()
for p in (ROOT/'preimage').rglob('*'):
 if p.is_file() and not any(r['path']==str(p.relative_to(ROOT/'preimage')) for r in changes):assert (ROOT/'candidate'/p.relative_to(ROOT/'preimage')).read_bytes()==p.read_bytes()
scope=json.loads((ROOT/'evidence/scope-and-static-checks.json').read_text());assert H((ROOT/'patches/lifecycle-from-gpio28-candidate.patch').read_bytes())==scope['patch_sha256']
hal=json.loads((ROOT/'inputs/prior/evidence/HAL-unchanged.json').read_text());assert H((W/hal['path']).read_bytes())==hal['sha256']
results=(ROOT/'evidence/corrected-final-run.txt').read_text();assert 'PASS lifecycle regressions: 12 scenarios' in results and '52 allocations matched 52 frees' in results
for name in ['lifetime-null','lifetime-routing-pm']:assert 'runtime error: member access within null pointer' in (ROOT/f'evidence/baseline-{name}-run.txt').read_text()
assert 'On accepted' in (ROOT/'evidence/baseline-lifetime-stale-suspend-run.txt').read_text()
report={'status':'PASS source-only package for fresh independent review','pinned_originals_and_copies_verified':len(pins),'changed_paths':len(changes),'patch_replay':'exact; fuzz0','inherited_scenarios':38,'new_lifecycle_scenarios':12,'allocation_free_balance':[52,52],'private_control_boundaries':46,'target_builds':0,'full_kernel_builds':0,'hardware_or_network_operations':0,'HAL_routes_qualified':False,'physical_GO':False,'command_state_only':True}
(ROOT/'evidence/final-verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
