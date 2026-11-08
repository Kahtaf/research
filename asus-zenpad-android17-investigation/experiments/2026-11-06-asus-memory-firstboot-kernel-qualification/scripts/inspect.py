"""One bounded SSH inspection; never executes a build or runtime fixture."""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[2]
SPIKE = Path(__file__).resolve().parents[1]
FILES = {
    'firstboot': ROOT/'2026-11-06-asus-firstboot-parity-continuation/artifacts/frozen-r3/evidence/combined-parity.json',
    'memory_sources': ROOT/'2026-11-06-asus-sdk37-lmkd-functional/artifacts/frozen/evidence/final-source-parity.json',
    'memory_config': ROOT/'2026-11-06-asus-sdk37-lmkd-functional/artifacts/frozen/evidence/final-config-parity.json',
    'memory_export': ROOT/'2026-11-06-asus-sdk37-lmkd-functional/artifacts/frozen/export-manifest.json',
    'physical_parent': ROOT/'2026-11-06-asus-bmc156-full-kernel/evidence/parent-firstboot-parity-acceptance.json',
    'physical_full': ROOT/'2026-11-06-asus-bmc156-full-kernel/evidence/full-verification.json',
}
authorities = {k: {'path': str(p.relative_to(ROOT)), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest(), 'data': json.loads(p.read_text())} for k,p in FILES.items()}
(SPIKE/'evidence/authorities.json').write_text(json.dumps(authorities, indent=2)+'\n')
payload = {k:v['data'] for k,v in authorities.items()}
spec = importlib.util.spec_from_file_location('authorized_remote', ROOT/'2026-11-06-asus-product-input-build-kit/scripts/remote.py')
remote = importlib.util.module_from_spec(spec)
spec.loader.exec_module(remote)
script = (SPIKE/'scripts/remote_inspect.py').read_text().replace('PAYLOAD = None', 'PAYLOAD = '+repr(payload))
result = remote.run(script)
receipt = json.loads(result)
(SPIKE/'evidence/remote-inspection.json').write_text(json.dumps(receipt, indent=2)+'\n')
print(json.dumps({'remote_receipt': receipt['remote_receipt'], 'source_mismatches': {k: [r['path'] for r in v if not r['equal_physical'] or not r['matches_frozen_virtual']] for k,v in receipt['sources'].items()}, 'selected_config_differences': receipt['selected_config_differences'], 'whole_config_differences': len(receipt['whole_config_differences'])}, indent=2))
