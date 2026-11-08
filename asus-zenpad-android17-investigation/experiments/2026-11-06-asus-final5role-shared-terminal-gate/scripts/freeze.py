"""Read-only public baseline capture. Writes only this new spike."""
from pathlib import Path
import hashlib, json, shutil

R = Path(__file__).resolve().parents[1]
B = R.parent / '2026-11-06-asus-stock-only-ram-rescue-build'
C = R.parent / '2026-11-06-asus-final5role-terminal-restore-contract'
V = R.parent / '2026-11-06-asus-final5role-terminal-restore-independent-review'

def pin(p):
    b = p.read_bytes()
    return dict(bytes=len(b), sha256=hashlib.sha256(b).hexdigest())

def inventory():
    expected = json.loads((B / 'SOURCE_PINS.json').read_text())
    rows = {}
    for rel, digest in expected.items():
        got = pin(B / rel)
        assert got['sha256'] == digest, rel
        rows[str((B / rel).relative_to(R.parent))] = got
    # Only named public artifacts; never keys/private input or arbitrary tree scans.
    for rel in ['SOURCE_PINS.json', 'ARTIFACTS.json', 'DELIVERY_PINS.json',
                'artifacts/original-stock.manifest', 'artifacts/restore-sepolicy',
                'artifacts/candidate/UNAPPROVED-STOCK-ONLY.img']:
        rows[str((B / rel).relative_to(R.parent))] = pin(B / rel)
    for base, rels in [(C, ['CONTRACT.md', 'WORK_AND_ACCEPTANCE.md',
                           'SOURCE_PINS.md', 'proposal/terminal-profile.patch.txt']),
                       (V, ['REPORT.md'])]:
        for rel in rels:
            rows[str((base / rel).relative_to(R.parent))] = pin(base / rel)
    img = (B / 'artifacts/candidate/UNAPPROVED-STOCK-ONLY.img').read_bytes()
    assert hashlib.sha256(img).hexdigest() == '5a61d3d65a7ba6b29745a965d9911ab4483c951a0327339839a0541bcb9ab30f'
    h = hashlib.sha256(img)
    h.update(bytes(16740352 - len(img)))
    assert h.hexdigest() == '3f99c785cca60bf56c2505711e2d26b72623daf28180515d44c5ba2abf03a44a'
    assert pin(B / 'artifacts/restore-sepolicy')['sha256'] == '16f6ce7f25c1b56aba9e4179573c49a6c55f9b9fe3f18336029f6d83b5b4b2c2'
    return dict(inputs=rows, frozen_padded_p10_sha256=h.hexdigest(),
                padded_file_created=False)

if __name__ == '__main__':
    (R / 'evidence').mkdir()
    before = inventory()
    (R / 'evidence/input-before.json').write_text(json.dumps(before, indent=2)+'\n')
    for d in ['baseline', 'source', 'inputs/design', 'NONDEPLOYABLE/tests',
              'NONDEPLOYABLE/include/sys', 'NONDEPLOYABLE/include/linux']:
        (R / d).mkdir(parents=True, exist_ok=True)
    for p in (B / 'source').iterdir():
        if p.suffix in ['.c', '.h']:
            shutil.copyfile(p, R / 'baseline' / p.name)
            shutil.copyfile(p, R / 'source' / p.name)
    for rel in ['CONTRACT.md', 'WORK_AND_ACCEPTANCE.md', 'SOURCE_PINS.md']:
        shutil.copyfile(C / rel, R / 'inputs/design' / rel)
    shutil.copyfile(C / 'proposal/terminal-profile.patch.txt', R / 'inputs/design/terminal-profile.patch.txt')
    shutil.copyfile(V / 'REPORT.md', R / 'inputs/design/independent-review.md')
    shutil.copyfile(B / 'SOURCE_PINS.json', R / 'inputs/SOURCE_PINS.json')
    shutil.copyfile(B / 'artifacts/original-stock.manifest', R / 'NONDEPLOYABLE/original-stock.manifest')
    print('Exact preimages captured; frozen image/padded hash/policy/source pins verified.')
