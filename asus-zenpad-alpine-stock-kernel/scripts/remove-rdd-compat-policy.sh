set -eu
python3 - <<'PY'
from pathlib import Path
import hashlib,os
p=Path('/usr/lib/firefox-esr/distribution/policies.json')
assert hashlib.sha256(p.read_bytes()).hexdigest()=='1f7d6968b0846b1b7563054e95b04e412c42324486642d9861321445dce7c11e'
p.unlink();os.sync()
print('EXACT_UNQUALIFIED_RDD_POLICY_REMOVED; owner profile preferences untouched')
PY
