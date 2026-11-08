"""Pin final offline review outputs without importing reviewed production code."""
import datetime
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True
from snapshot import ROOT, WS, PARENT, digest

def main():
    relative_receipts = [
        'snapshot/2026-11-06-asus-rescue-pin-monotonic-fix/evidence/offline-1794006389677503000/receipt.json',
        'snapshot/2026-11-06-asus-rescue-pin-monotonic-fix/evidence/targeted-1794006389677542000/receipt.json',
        'evidence/fresh-1794006533988862000/receipt.json',
    ]
    tests = []
    for relative in relative_receipts:
        receipt = json.loads((ROOT / relative).read_text())
        assert receipt['failures'] == receipt['errors'] == 0
        assert receipt['audit_blocked_events'] == []
        assert receipt['code']['sha256'] == '24196e415ac61a56fac5ef1ce145181c90915323129600cc16d67096d1afc62e'
        tests.append({'path': relative, 'sha256': digest(ROOT / relative), 'methods': receipt['tests']})
    assert sum(t['methods'] for t in tests) == 80
    for receipt_path in (ROOT / 'evidence').glob('fresh-*/receipt.json'):
        receipt = json.loads(receipt_path.read_text())
        assert digest(receipt_path.parent / 'fresh_review.py') == receipt['test_sha256']
    preservation = json.loads((ROOT / 'evidence/preservation.json').read_text())
    originals = json.loads((ROOT / 'evidence/originals.before.json').read_text())
    assert originals == json.loads((ROOT / 'evidence/originals.after.json').read_text())
    code = preservation['current_code']
    assert code == json.loads((PARENT / 'HANDOFF.json').read_text())['code']
    for name, pin in code['files'].items():
        assert digest(PARENT / name) == pin
        assert digest(ROOT / 'snapshot' / PARENT.name / name) == pin
    excluded = {'HANDOFF.json', 'evidence/artifacts.sha256.json'}
    artifacts = {str(path.relative_to(ROOT)): digest(path) for path in sorted(ROOT.rglob('*'))
                 if path.is_file() and not path.is_symlink() and
                 str(path.relative_to(ROOT)) not in excluded}
    manifest = ROOT / 'evidence/artifacts.sha256.json'
    manifest.write_text(json.dumps(artifacts, indent=2, sort_keys=True) + '\n')
    handoff = dict(
        utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        status='independent offline review complete; previous R1 closed in tested scope; no concrete delta defects found',
        scope='exact host-side USB-pin clock-rollback transport fix and relevant historical install/removal linkage',
        findings=[], requested_source_fixes=[], code=code,
        original_code_sha256=preservation['original_code']['sha256'],
        tests=tests, final_methods=80, final_failures=0, final_errors=0,
        actual_production_subprocess_operations=0, actual_network_operations=0, actual_device_operations=0,
        original_files_verified=preservation['original_file_count'],
        original_files_compared_to_prior_review=51, original_public_inputs_verified=16,
        preservation_receipt={'path': 'evidence/preservation.json', 'sha256': digest(ROOT / 'evidence/preservation.json')},
        report={'path': 'REPORT.md', 'sha256': digest(ROOT / 'REPORT.md')},
        artifacts={'path': 'evidence/artifacts.sha256.json', 'sha256': digest(manifest), 'files': len(artifacts)},
        fixture_corrections='Initial fresh suite had three owned-contract-path fixture failures. Exact initial and corrected source/logs retained; copied production code unchanged.',
        authority='No execution approval, affirmative operational flags, or physical GO supplied. Parent owns every real action.',
        limits='No physical/transport/boot/timing success. No target rescue, LK, or audio re-review. No network, device, ADB, root, SSH, VM, cloud, or build actions.')
    (ROOT / 'HANDOFF.json').write_text(json.dumps(handoff, indent=2) + '\n')
    print(json.dumps({'report': str(ROOT / 'REPORT.md'), 'handoff': str(ROOT / 'HANDOFF.json'),
                      'final_methods': 80, 'findings': 0, 'artifact_files': len(artifacts)}))

if __name__ == '__main__':
    main()
