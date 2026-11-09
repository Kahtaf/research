set -eu
cat /run/asus-alpine/sd-root-build.json
cat /proc/mounts | awk '$2=="/" || $2=="/mnt/asus-root-stage" || $2=="/mnt/alpine-sd"'
df -h / /mnt/asus-root-stage /mnt/alpine-sd
python3 - <<'PY'
from pathlib import Path
import json
d=json.loads(Path('/run/asus-alpine/sd-root-build.json').read_text())
assert d['phase']=='POPULATED_AND_SELECTED_FILES_VERIFIED'
assert Path(d['image']).stat().st_size==2147483648
profile=Path('/mnt/asus-root-stage/root/.mozilla/asus-appliance')
assert (profile/'prefs.js').is_file()
print('STAGED_BROWSER_PROFILE_PRESENT')
p=Path('/run/asus-alpine/udhcpc.pid').read_text().strip()
print('DHCP_PROCESS',Path('/proc',p,'cmdline').read_bytes().replace(b'\0',b' ').decode())
PY
tail -12 /run/asus-alpine/udhcpc.log
ip -4 addr show wlan0 | sed -n '1,4p'
