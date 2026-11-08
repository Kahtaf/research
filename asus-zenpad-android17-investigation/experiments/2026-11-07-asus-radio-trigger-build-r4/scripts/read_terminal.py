"""Small terminal receipts only; no image rehash or native invocation."""
from pathlib import Path
import hashlib
import json

OWN = Path('/srv/android/asus-radio-trigger-build-r4')
def digest(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
result = {'owned_prefix': str(OWN), 'native_limits': json.loads((OWN / 'attempt/address-space.json').read_text()),
          'terminal': {}, 'new_raw': None, 'new_mtkboot': None}
for name in ('started.json', 'integration.json', 'native-terminal.json', 'complete.json', 'FAILED.json', 'preserved-prior-receipts.json'):
    p = OWN / 'attempt' / name
    if p.exists(): result['terminal'][name] = {'value': json.loads(p.read_text()), 'sha256': digest(p)}
need_terminal = (OWN / 'attempt/complete.json').exists() or (OWN / 'attempt/FAILED.json').exists()
assert need_terminal, 'Execution is not terminal'
critical = OWN / 'critical-checks.json'
if critical.exists():
    result['critical_checks'] = json.loads(critical.read_text())
    result['critical_receipt_sha256'] = digest(critical)
    result['new_raw'] = result['critical_checks']['new_raw_system']
    result['new_mtkboot'] = result['critical_checks']['mtkboot']
result['check_receipts'] = {}
for name in ('packaging.json', 'runtime-linkerconfig.json', 'health-filter.json', 'netd-binding.json', 'root.json'):
    p = OWN / 'checks/r1' / name
    if p.exists(): result['check_receipts'][name] = {'value': json.loads(p.read_text()), 'sha256': digest(p)}
result['logs'] = {}
for p in (OWN / 'logs').glob('*.log'):
    with p.open('rb') as f:
        f.seek(max(0, p.stat().st_size - 9000))
        result['logs'][p.name] = {'path': str(p), 'bytes': p.stat().st_size, 'sha256': digest(p),
                                'tail': f.read().decode(errors='replace')}
result['old_raw_metadata_unchanged'] = True
for row in json.loads((OWN / 'attempt/old-raw-stat-pins.json').read_text()):
    st = Path(row['path']).stat()
    if (st.st_size, st.st_ino, st.st_mtime_ns, st.st_mode) != (row['bytes'], row['inode'], row['mtime_ns'], row['mode']):
        result['old_raw_metadata_unchanged'] = False
result['old_raw_rehashed'] = False
result['source_execution_code_sha256'] = {p.name: digest(p) for p in (OWN / 'scripts').glob('*') if p.is_file()}
print(json.dumps(result))
