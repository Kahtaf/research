#!/usr/bin/env python3
"""Offline artifact generation; fixed files only, no transports or payload reads."""
import difflib
import hashlib
import json
from pathlib import Path
import sys

SPIKE = Path(__file__).resolve().parents[1]
WORKSPACE = SPIKE.parent
BASELINE = WORKSPACE/'2026-11-06-asus-stock-system-wifi-backup'
sys.path.insert(0, str(SPIKE/'source'))
import continuation
import stock_system_backup as coordinator


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    baseline = json.loads((SPIKE/'evidence/input-baseline.json').read_text())
    preservation = {name: dict(expected=expected, actual=digest(WORKSPACE/name))
                    for name, expected in baseline.items()}
    if any(row['actual'] != row['expected'] for row in preservation.values()):
        raise SystemExit('Original selected input changed; inspect preservation report before handoff')
    prepared = json.loads((SPIKE/'evidence/prepared-input.json').read_text())
    candidate = SPIKE/'evidence/inputs'/(prepared['input_sha256']+'.json')
    bundle = json.loads(candidate.read_text())
    continuation.validate_input(bundle, prepared['input_sha256'])
    changes = []
    for folder in ('source', 'tests'):
        for path in sorted((SPIKE/folder).glob('*.py')):
            old = BASELINE/folder/path.name
            changes.extend(difflib.unified_diff(old.read_text().splitlines(True) if old.exists() else [],
                path.read_text().splitlines(True), fromfile=str(old.relative_to(WORKSPACE)) if old.exists() else '/dev/null',
                tofile=str(path.relative_to(WORKSPACE))))
    old = WORKSPACE/'2026-11-06-asus-wifi-device-access/scripts/root_shell_wifi.py'
    new = SPIKE/'scripts/root_shell_batched.py'
    changes.extend(difflib.unified_diff(old.read_text().splitlines(True),new.read_text().splitlines(True),
                    fromfile=str(old.relative_to(WORKSPACE)),tofile=str(new.relative_to(WORKSPACE))))
    (SPIKE/'evidence/adapter.diff').write_text(''.join(changes))
    tests = json.loads((SPIKE/'evidence/offline-tests.json').read_text())
    if tests['failures'] or tests['errors']:
        raise SystemExit('Offline checks did not pass')
    files = []
    for folder in ('source','scripts','tests'):
        files.extend(sorted((SPIKE/folder).glob('*.py')))
    files += [SPIKE/'README.md', SPIKE/'REPORT.md']
    files += sorted((SPIKE/'evidence').glob('*.json'))
    files += [SPIKE/'evidence/adapter.diff', SPIKE/'evidence/offline-tests.txt']
    files += sorted((SPIKE/'evidence/inputs').glob('*.json'))
    files = [path for path in files if path.name != 'source-review.json']
    optional = WORKSPACE/'2026-11-06-asus-stock-firmware-restore-source/evidence/audit.json'
    report = dict(status='offline implementation verified; parent review/execution outstanding',
                  tests_passed=tests['tests_run'], transport_executed=False, device_contacted=False,
                  ssh_contacted=False, vm_contacted=False, cloud_contacted=False,
                  selected_input_sha256=prepared['input_sha256'], prefix_chunks=len(bundle['chunks']),
                  selected_journal_files=len(bundle['journal_sha256']),
                  current_source_code_sha256=coordinator.local_inputs(),
                  current_helper_sha256=coordinator.HELPER_HASH,
                  root_binary_sha256=coordinator.ROOT_BINARY_HASH,
                  original_inputs_unchanged=True, original_input_recheck=preservation,
                  capture_dependencies_sha256=bundle['dependency_sha256'],
                  oem_audit_metadata_sha256={str(optional.relative_to(WORKSPACE)):digest(optional)},
                  artifacts_sha256={str(path.relative_to(SPIKE)):digest(path) for path in files},
                  excluded='No failed-run payload, private stage, calibration, userdata or private key was read',
                  claims='No live backup or restore result; no fresh contiguous aggregate source-pass hash')
    (SPIKE/'evidence/source-review.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
    print(json.dumps(dict(tests_passed=tests['tests_run'],selected_input_sha256=prepared['input_sha256'],
                         original_inputs_unchanged=True,artifacts_hashed=len(files)),indent=2))


if __name__ == '__main__':
    main()
