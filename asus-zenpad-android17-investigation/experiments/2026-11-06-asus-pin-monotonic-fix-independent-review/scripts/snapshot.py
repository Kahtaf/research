"""Copy only named public inputs and reviewed files; preserve originals in place."""
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
WS = ROOT.parent
PARENT = WS / '2026-11-06-asus-rescue-pin-monotonic-fix'
ORIGINAL = WS / '2026-11-06-asus-exact-rescue-recovery-adapter'
PRIOR = WS / '2026-11-06-asus-exact-recovery-adapter-independent-review'

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def manifest(directory):
    return {str(p.relative_to(WS)): digest(p) for p in sorted(directory.rglob('*'))
            if p.is_file() and not p.is_symlink()}

def save(name, value):
    (ROOT / 'evidence' / name).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')

def main():
    (ROOT / 'evidence').mkdir(exist_ok=True)
    before = {}
    for directory in (PARENT, ORIGINAL, PRIOR):
        before.update(manifest(directory))
    inputs = json.loads((PARENT / 'evidence/original-inputs.before.json').read_text())
    extra = '2026-11-06-asus-linux49-probe-initrd-fix/artifacts/probe-r3/UNTESTED-combined-linux49-ram-probe-r3.img'
    inputs[extra] = digest(WS / extra)
    for name, expected in inputs.items():
        assert digest(WS / name) == expected, name
        before[name] = expected
        target = ROOT / 'snapshot' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(WS / name, target)
    rels = ['profile.json', 'HANDOFF.md', 'HANDOFF.json', 'README.md',
            'evidence/original-inputs.before.json', 'evidence/adapter-fix.patch',
            'scripts/reviewer_regressions.py']
    rels += [str(p.relative_to(PARENT)) for sub in ('source', 'tests')
             for p in sorted((PARENT / sub).rglob('*')) if p.is_file() and '__pycache__' not in p.parts]
    for name in rels:
        source = PARENT / name
        target = ROOT / 'snapshot' / PARENT.name / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        assert digest(target) == digest(source)
    # Preserve baseline source and finding for review, without importing old production code.
    for source in (ORIGINAL / 'source/adapter.py', PRIOR / 'REPORT.md',
                   PRIOR / 'scripts/targeted_review.py'):
        target = ROOT / 'snapshot' / source.relative_to(WS)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    save('originals.before.json', before)
    save('inputs.json', inputs)
    save('snapshot.before.json', manifest(ROOT / 'snapshot'))
    print(json.dumps({'protected_original_files': len(before), 'public_inputs': len(inputs),
                      'snapshot_files': len(manifest(ROOT / 'snapshot'))}))

if __name__ == '__main__':
    main()
