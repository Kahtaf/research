"""Verify exact production/test/template provenance without private payload reads."""
import hashlib
import json
from pathlib import Path
import sys

R = Path(__file__).resolve().parents[1]
W = R.parent
P = W / '2026-11-06-asus-stock-roundtrip-parent-fixes'
sys.dont_write_bytecode = True
sys.path.insert(0, str(P / 'source/service'))
import controller as C
import transport as T

sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
before = json.loads((R / 'evidence/parent-before.json').read_text())
after = {str(p.relative_to(W)): sha(p) for p in P.rglob('*') if p.is_file() and not p.is_symlink()}
assert before == after, 'Parent files changed during review; inspect before handoff'
pins = json.loads((P / 'evidence/verified-source-pins.json').read_text())
assert all(sha(P / k) == v for k, v in pins.items())
copied = {p.name: sha(p) for p in (R / 'tests/service').glob('test_*.py')}
assert all(v == sha(P / 'tests/service' / name) for name, v in copied.items())
verification = json.loads((P / 'evidence/verification.json').read_text())
template = Path(verification['plan']['evidence']) / 'review-template.json'
value = json.loads(template.read_text())
assert value == C.template()
assert all(x is False for x in value['parent_review'].values() if type(x) is bool)
assert sha(C.F.ENGINE) == C.F.ENGINE_SHA
contract = dict(source_and_evidence_sha256=C.source_pins(), template_path=str(template),
                template_sha256=sha(template), contract_matches_current_source=True,
                live_flags_all_false=True,
                production_imports={m.__name__: m.__file__ for m in (C, C.F, C.O, T)},
                helper_sha256=C.E.HELPER_HASH, engine_sha256=C.F.ENGINE_SHA,
                private_payloads_read=False, device_contacted=False)
(R / 'evidence/verified-contract.json').write_text(json.dumps(contract, indent=2) + '\n')
receipt = dict(parent_files_unchanged=True, parent_file_count=len(after), copied_tests_sha256=copied,
               expected_parent_source_pins=pins, frozen_engine_matches=True,
               template_matches=True, all_live_flags_false=True, device_contacted=False)
(R / 'evidence/provenance.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps({k: v for k, v in receipt.items() if not isinstance(v, dict)}))
