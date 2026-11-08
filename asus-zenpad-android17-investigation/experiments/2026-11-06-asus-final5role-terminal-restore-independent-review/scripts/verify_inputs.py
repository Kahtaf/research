"""Read-only SHA256/length inspection of the delivered 69 public inputs."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
OWN = Path(__file__).resolve().parents[1]
DESIGN = ROOT / '2026-11-06-asus-final5role-terminal-restore-contract'

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return dict(sha256=h.hexdigest(), bytes=path.stat().st_size)

pins = json.loads((DESIGN / 'evidence/INPUT_PINS.json').read_text())
rows = []
for name, expected in pins.items():
    actual = digest(ROOT / name)
    rows.append(dict(path=name, expected=expected, actual=actual, passed=actual == expected))
handoff = json.loads((DESIGN / 'HANDOFF.json').read_text())
docs = []
for name, expected in handoff['documents'].items():
    actual = digest(DESIGN / name)
    docs.append(dict(path=name, expected_sha256=expected, actual=actual,
                     passed=actual['sha256'] == expected))
result = dict(public_input_count=len(rows), passed=len(rows) == 69 and all(r['passed'] for r in rows),
              inputs=rows, design_documents=docs,
              design_document_pins_match=all(r['passed'] for r in docs))
(OWN / 'evidence/input-verification.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({k: v for k, v in result.items() if k not in ('inputs', 'design_documents')}))
assert result['passed'] and result['design_document_pins_match']
