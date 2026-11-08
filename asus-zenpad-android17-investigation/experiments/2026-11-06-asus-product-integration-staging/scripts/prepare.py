#!/usr/bin/env python3
"""Create a pinned, isolated builder candidate. Default PLAN_ONLY."""
from pathlib import Path
import argparse
import base64
import hashlib
import json
import shlex
import subprocess

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT.parent
HANDOFF = WORK / '2026-11-06-asus-combined-kernel-integration/artifacts/handoff-r5'
PACK = WORK / '2026-11-06-asus-full-boot-lk-contract'
BASE = WORK / '2026-11-06-asus-android17-build-continuation'
EXPECTED = {
    'Image.gz-dtb': '46895deb12ec94160ea5af0e85afa89c6de84971db126bb94c60cec1ec3ec401',
    'resolved.config': '067090e03ad762344308cebd0a71274d9943e299ded6707051ebfdc075dd045f',
    'manifest.json': None,
    'staged-product-receipt.json': '085c3e0febdb4dcac5d8b8235ee6aa7da8adcdb8ce0af3a7bd1366fb0a527b7d',
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def prepare_payload():
    checks = json.loads((PACK / 'evidence/checks.json').read_text())
    if checks['status'] != 'PASS' or any(s['exit_code'] for s in checks['steps']):
        raise ValueError('Packaging checks have not passed')
    pins = {}
    for name, expected in EXPECTED.items():
        actual = sha((HANDOFF / name).read_bytes())
        if expected is not None and actual != expected:
            raise ValueError('Local handoff changed: ' + name)
        pins[name] = actual
    receipts = json.loads((PACK / 'evidence/integration-receipts.json').read_text())
    files = {}
    for rel, item in receipts.items():
        origin = PACK if 'after_sha256' in item else BASE
        raw = (origin / rel).read_bytes()
        expected = item.get('after_sha256', item.get('unchanged_dependency_sha256'))
        if sha(raw) != expected:
            raise ValueError('Packaging source changed: ' + rel)
        files[rel] = {'sha256': expected, 'base64': base64.b64encode(raw).decode()}
    return {'handoff_pins': pins, 'packaging_files': files}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', action='store_true')
    args = parser.parse_args()
    payload = prepare_payload()
    if not args.stage:
        print(json.dumps({'mode': 'PLAN_ONLY', 'remote_contacted': False,
                          'kernel_sha256': payload['handoff_pins']['Image.gz-dtb'],
                          'packaging_files': len(payload['packaging_files']),
                          'active_deployment': False}, indent=2))
        return
    evidence = ROOT / 'evidence/remote-staging.json'
    if evidence.exists():
        raise ValueError('Preserve existing parent receipt')
    remote = (ROOT / 'scripts/remote_stage.py').read_text()
    command = ['ssh', '-i', str(Path.home() / '.ssh/asus_p00a_android17'),
               '-o', 'IdentitiesOnly=yes', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15',
               '-o', 'StrictHostKeyChecking=yes', '-o', 'HostKeyAlias=compute.8549823276971553556',
               '-o', 'UserKnownHostsFile=' + str(Path.home() / '.ssh/google_compute_known_hosts'),
               'android@IP_REDACTED', 'python3 -c ' + shlex.quote(remote)]
    result = subprocess.run(command, input=json.dumps(payload), text=True,
                            capture_output=True, timeout=120)
    (ROOT / 'evidence/stage-stdout.txt').write_text(result.stdout)
    (ROOT / 'evidence/stage-stderr.txt').write_text(result.stderr)
    result.check_returncode()
    record = json.loads(result.stdout)
    if record['handoff_pins'] != payload['handoff_pins'] or not record['active_product_unchanged']:
        raise ValueError('Remote staging receipt mismatch')
    evidence.write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps({'status': record['status'], 'path': record['path'],
                      'changed_product_paths': sorted(record['changes_from_radio_candidate']),
                      'active_product_unchanged': True, 'build_started': False,
                      'physical_boot_verified': False}, indent=2))


if __name__ == '__main__':
    main()
