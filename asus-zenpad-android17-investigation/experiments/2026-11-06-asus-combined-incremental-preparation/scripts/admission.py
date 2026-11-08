"""Exact source-map and parent/namespace admission; no active-tree access."""
from pathlib import Path, PurePosixPath
import hashlib
import json
import re

ROOT_MK = '9eef1d1e5463f43500863604641f8fb3af8d91fb9100b83f231b216041f79c75'
KIT = '744fa117bba0e4ba9895af792ddc71f1cbe99196cb752593e560064ef8d41e69'
def need(value, message):
    if not value:
        raise ValueError(message)
def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):
    return json.loads(Path(path).read_text())
def digest(value):
    return isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value) is not None
def relative(value):
    p = PurePosixPath(value)
    need(not p.is_absolute() and '..' not in p.parts and p.parts and p.parts[0] not in ('out', '.git'), 'Unsafe source path')
    return value
def compose(base, journal):
    need(journal['status'] == 'SOURCE_INTEGRATED_NATIVE_BUILD_PENDING' and journal['all_postimages_verified'] is True, 'Unaccepted profile integration')
    need(len(journal['changes']) == 10 and len({r['path'] for r in journal['changes']}) == 10, 'Exact ten profile files required')
    result = dict(base)
    for row in journal['changes']:
        path = relative(row['path'])
        need(path.startswith('device/asus/p00a/') and path != 'device/asus/p00a/lineage_p00a.mk', 'Profile source scope changed')
        rel = path.removeprefix('device/asus/p00a/')
        need((base.get(rel) or {}).get('sha256') == row['before_sha256'], 'Profile preimage mismatch: ' + rel)
        need(digest(row['after_sha256']), 'Missing profile postimage')
        result[rel] = {'sha256': row['after_sha256']}
    need(result['lineage_p00a.mk'] == {'sha256': ROOT_MK}, 'Incorrect root MK')
    return result
def check_source_map(actual, expected):
    need(actual.get('lineage_p00a.mk') == {'sha256': ROOT_MK}, 'Incorrect root MK')
    need(actual == expected, 'Unknown, missing or changed source in product manifest')
def admit(home, namespace_path, acceptance_path):
    home = Path(home)
    need(namespace_path is not None and Path(namespace_path).is_file(), 'Namespace handoff is missing; execution forbidden')
    need(acceptance_path is not None and Path(acceptance_path).is_file(), 'Exact parent acceptance is missing; execution forbidden')
    ns_path, approval_path = Path(namespace_path), Path(acceptance_path)
    ns, approval = read(ns_path), read(approval_path)
    need(ns['owner'] == 'e90477dc' and ns['purpose'] == 'heapprofd_client_api.so namespace ownership repair', 'Wrong namespace handoff owner/scope')
    need(approval['authorize_native_execution'] is True and approval['reviewed_by_parent'] is True and approval['instruction'].strip(), 'No exact parent build authorization')
    need(approval['namespace_handoff_sha256'] == sha(ns_path), 'Unbound namespace handoff')
    need(approval['profile_expected_sha256'] == sha(home / 'inputs/expected-profile-product.json'), 'Wrong profile source baseline')
    need(approval['preparation_pins_sha256'] == sha(home / 'inputs/owned-code-pins.json'), 'Prepared code pins not accepted')
    need(approval['native_command'] == ['m', '-j4', 'systemimage', 'bootimage'], 'Unapproved native command')
    patch = ns_path.parent / ns['patch_file']
    proof_path = ns_path.parent / ns['compiled_proof_file']
    need(patch.is_file() and proof_path.is_file(), 'Namespace patch/compiled proof not delivered')
    need(sha(patch) == ns['patch_sha256'] == approval['namespace_patch_sha256'], 'Namespace patch binding mismatch')
    need(sha(proof_path) == ns['compiled_proof_sha256'] == approval['compiled_proof_sha256'], 'Compiled proof binding mismatch')
    changes = ns['changes']
    need(changes and changes == approval['approved_source_changes'], 'Namespace source allowlist differs from parent acceptance')
    forbidden = {r['path'] for r in read(home / 'inputs/profile-journal.json')['changes']} | {'device/asus/p00a/lineage_p00a.mk'}
    need(len({r['path'] for r in changes}) == len(changes), 'Duplicate namespace source paths')
    expected = read(home / 'inputs/expected-profile-product.json')
    for row in changes:
        path = relative(row['path'])
        need(path not in forbidden and not path.startswith(('kernel/', 'prebuilts/', 'system/sepolicy/', 'device/asus/p00a/sepolicy/')) and '/prebuilt/' not in path and not path.endswith('BoardConfig.mk'), 'Namespace repair changes protected source')
        need(digest(row['before_sha256']) and digest(row['after_sha256']) and row['before_sha256'] != row['after_sha256'], 'Unproved namespace source delta')
        payload = ns_path.parent / row['payload_file']
        need(payload.is_file() and sha(payload) == row['after_sha256'], 'Namespace source payload missing/wrong')
        if path.startswith('device/asus/p00a/'):
            rel = path.removeprefix('device/asus/p00a/')
            need(expected.get(rel) == {'sha256': row['before_sha256']}, 'Namespace device preimage differs')
            expected[rel] = {'sha256': row['after_sha256']}
    proof = read(proof_path)
    need(proof['genuine_compiled_verification'] is True and proof['fixture_only'] is False and proof['passed'] is True, 'No genuine compiled namespace proof')
    need(proof['patch_sha256'] == sha(patch) and proof['source_postimages'] == {r['path']: r['after_sha256'] for r in changes}, 'Compiled proof source binding mismatch')
    need(proof['commands'] and all(r['exit'] == 0 for r in proof['commands']), 'Compiled namespace verification failed/missing')
    need(proof['evidence_files'], 'No compiled evidence artifacts/logs')
    for row in proof['evidence_files']:
        need(sha(ns_path.parent / row['file']) == row['sha256'], 'Compiled proof evidence changed')
    checker = proof['final_checker']
    need(checker['argv'] and digest(checker['tool_sha256']) and checker['assertions_relaxed'] is False, 'Final genuine namespace checker is unbound')
    return {'authorized': True, 'namespace_handoff': str(ns_path.resolve()), 'namespace_sha256': sha(ns_path),
            'parent_acceptance': str(approval_path.resolve()), 'parent_acceptance_sha256': sha(approval_path),
            'namespace': ns, 'proof': proof, 'expected_product': expected,
            'profile_expected_sha256': sha(home / 'inputs/expected-profile-product.json')}
def require_binding(home):
    home = Path(home)
    path = home / 'binding.json'
    need(path.is_file(), 'Namespace/parent acceptance unbound; no native launch or active source access permitted')
    binding = read(path)
    actual = admit(home, binding['namespace_handoff'], binding['parent_acceptance'])
    need(actual == binding, 'Admission binding changed')
    return binding
if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--home', type=Path, default=Path(__file__).resolve().parents[1])
    p.add_argument('--namespace', type=Path)
    p.add_argument('--acceptance', type=Path)
    p.add_argument('--bind', action='store_true')
    args = p.parse_args()
    try:
        value = admit(args.home, args.namespace, args.acceptance)
        if args.bind:
            with (args.home / 'binding.json').open('x') as f: json.dump(value, f, indent=2); f.write('\n')
        print(json.dumps({'status': 'BOUND' if args.bind else 'ADMISSION_CHECKED', 'authorized': True}))
    except (ValueError, KeyError, OSError) as e:
        print(json.dumps({'status': 'UNBOUND_REFUSED', 'authorized': False, 'reason': str(e)}))
        raise SystemExit(20)
