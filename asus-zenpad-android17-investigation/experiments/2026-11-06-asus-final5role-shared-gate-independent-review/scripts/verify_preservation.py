"""Read-only public pin verification; writes only review evidence."""
from pathlib import Path
import hashlib, json, shlex, sys
R = Path(__file__).resolve().parents[1]
W = R.parent
I = W / '2026-11-06-asus-final5role-shared-terminal-gate'
B = W / '2026-11-06-asus-stock-only-ram-rescue-build'
E = I / 'evidence/run-20261106-192903'
sys.path.insert(0, str(R / 'scripts'))
from freeze import inventory

def pin(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda: f.read(1048576), b''):
            h.update(b)
    return dict(bytes=p.stat().st_size, sha256=h.hexdigest())

def check_map(p, base):
    rows = json.loads(p.read_text())
    for name, value in rows.items():
        assert pin(base / name) == value, (p, name)
    return len(rows)

counts = {'review_inputs': check_map(R / 'evidence/review-input-before.json', W)}
for label, base in [('compiled-input-pins', Path('/')), ('test-input-pins', I),
                    ('native-product-pins', I / 'NONDEPLOYABLE/run-20261106-192903/bin')]:
    counts[label] = check_map(E / (label + '.json'), base)
prepost = json.loads((E / 'source-prepost.json').read_text())
assert len(prepost) == 13
for name, values in prepost.items():
    for side, folder in [('pre', 'baseline'), ('post', 'source')]:
        p = I / folder / name
        assert (pin(p) == values[side]) if p.exists() else values[side] is None
        if p.exists():
            assert pin(p) == pin(R / folder / name)
    if values['pre'] is not None:
        assert pin(I / 'baseline' / name) == pin(B / 'source' / name)
assert sorted(p.name for p in (I / 'source').iterdir()) == sorted(prepost)
changed = [n for n, v in prepost.items() if v['pre'] != v['post']]
assert changed == ['handoff.h', 'p10_restore.c', 'terminal_profile.h']
assert not (I / 'source/terminal_manifest_binding.h').exists()
assert not (R / 'source/terminal_manifest_binding.h').exists()
C = W / '2026-11-06-asus-final5role-terminal-restore-contract'
proposal = C / 'proposal/terminal-profile.patch.txt'
assert (I / 'terminal-profile.patch').read_bytes() == proposal.read_bytes() == (R / 'terminal-profile.patch').read_bytes()
assert (I / 'inputs/design/CONTRACT.md').read_bytes() == (C / 'CONTRACT.md').read_bytes()
assert inventory() == json.loads((I / 'evidence/input-before.json').read_text()) == json.loads((E / 'input-after.json').read_text())
tool = json.loads((E / 'toolchain.json').read_text())
for key, p in [('python_pin', Path(tool['python_executable'])),
               ('clang_pin', Path('/usr/bin/clang')),
               ('actual_clang_pin', Path('/Library/Developer/CommandLineTools/usr/bin/clang')),
               ('linker_pin', Path('/Library/Developer/CommandLineTools/usr/bin/ld'))]:
    assert pin(p) == tool[key], key
headers = {}
run = I / 'NONDEPLOYABLE/run-20261106-192903'
for shape in ['full', 'small']:
    header = run / 'bindings' / shape / 'terminal_manifest_binding.h'
    for context in ['DAEMON_ONLY', 'HELPER_ONLY']:
        text = (run / 'bin' / (shape + '-' + context + '.d')).read_text()
        dependencies = {Path(p).resolve() for p in shlex.split(text.replace('\\\n', ' ').split(':', 1)[1])}
        assert header in dependencies, (shape, context)
        assert I / 'source/terminal_profile.h' in dependencies
    headers[shape] = dict(header=str(header), pin=pin(header))
for run_name in ['run-20261106-193356', 'run-20261106-193614']:
    for label, base in [('compiled-input-pins', Path('/')), ('test-input-pins', R),
                        ('native-product-pins', R / 'NONDEPLOYABLE' / run_name / 'bin')]:
        counts[run_name + '/' + label] = check_map(R / 'evidence' / run_name / (label + '.json'), base)
    assert json.loads((R / 'evidence' / run_name / 'summary.json').read_text())['passed']
rows = json.loads((R / 'evidence/review-input-before.json').read_text())
after = {name: pin(W / name) for name in rows}
assert rows == after
(R / 'evidence/review-input-after.json').write_text(json.dumps(after, indent=2) + '\n')
result = dict(passed=True, counts=counts, source_prepost=13, changed=changed,
              proposal_pin=pin(proposal), baseline_equals_frozen=True,
              original_public_inventory_equal=True, production_binding_absent=True,
              shared_compiled_headers=headers, implementation_and_existing_evidence_unchanged=True)
(R / 'evidence/pin-verification.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
