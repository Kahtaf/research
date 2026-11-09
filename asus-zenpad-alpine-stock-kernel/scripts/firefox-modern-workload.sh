set -eu
mkdir -p /run/asus-goodix
nonce=$(python3 -c 'import secrets; print(secrets.token_hex(12))')
setsid timeout -k 2 70 /usr/bin/python3 /tmp/browser-workload.py --nonce "$nonce" --output /run/asus-goodix/browser-proof.json </dev/null > /run/asus-goodix/browser-workload.log 2>&1 &
server=$!
trap 'kill "$server" 2>/dev/null || true' EXIT
sleep 1
XDG_RUNTIME_DIR=/run/user/0 timeout -k 2 40 firefox-esr --headless --no-remote --profile /tmp/firefox-modern-proof --screenshot /tmp/firefox-modern-proof.png --window-size 800,1280 http://127.0.0.1:8081/
python3 - <<'PY'
import json
from pathlib import Path
p=Path('/run/asus-goodix/browser-proof.json');d=json.loads(p.read_text());assert d['passed'] and all(d[k] for k in ('modernJavaScript','fetch','canvas','localStorage','indexedDB')),d
assert 'Firefox/140.0' in d['userAgent'],d['userAgent']
print(json.dumps(d,indent=2));print('REAL_FIREFOX_MODERN_BROWSER_WORKLOAD_PASS')
PY
