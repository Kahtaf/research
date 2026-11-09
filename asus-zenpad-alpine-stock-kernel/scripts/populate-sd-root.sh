set -eu
set -o pipefail
T=/mnt/asus-root-stage
python3 - <<'PY'
from pathlib import Path
import json,os
run=Path('/run/asus-alpine');d=json.loads((run/'sd-root-build.json').read_text())
assert d['phase']=='EXT4_2GIB_RW_PASS_READY_TO_POPULATE'
assert Path(d['image']).stat().st_size==2147483648
assert os.path.ismount('/mnt/asus-root-stage')
for entry in Path('/proc').iterdir():
 if not entry.name.isdecimal():continue
 try:args=(entry/'cmdline').read_bytes().split(b'\0')
 except (FileNotFoundError,ProcessLookupError):continue
 assert b'/root/.mozilla/asus-appliance' not in args,'Interactive Firefox is not closed'
d['phase']='COPYING_CLOSED_OS_AND_BROWSER_PROFILE';(run/'sd-root-build.json').write_text(json.dumps(d)+'\n')
PY
if [ ! -s /etc/machine-id ]; then
 tr -d '-' < /proc/sys/kernel/random/uuid > /etc/machine-id
 chmod 444 /etc/machine-id
fi
mkdir -p /var/lib/dbus
[ -e /var/lib/dbus/machine-id ] || ln -s /etc/machine-id /var/lib/dbus/machine-id
tar -cf - \
 --exclude='./proc' --exclude='./sys' --exclude='./dev' --exclude='./run' \
 --exclude='./tmp' --exclude='./mnt' --exclude='./system' --exclude='./data' \
 --exclude='./etc/asus-alpine' --exclude='./etc/ssh/ssh_host*' \
 --exclude='./var/lib/asus-dashboard' --exclude='./var/log' \
 -C / . | tar -xf - -C "$T"
mkdir -p "$T/dev" "$T/proc" "$T/sys" "$T/run" "$T/tmp" "$T/system" "$T/mnt/alpine-sd" "$T/data" "$T/etc/asus-alpine" "$T/var/lib/asus-dashboard" "$T/var/log"
chmod 1777 "$T/tmp"
[ "$(cat "$T/etc/asus-alpine-ram-release")" = asus-alpine-stock-kernel-v1 ]
chroot "$T" /bin/busybox sh -ec 'cat /etc/alpine-release; uname -rm; test -x /usr/bin/firefox-esr; test -x /usr/local/bin/asus-goodix-desktop'
python3 - <<'PY'
from pathlib import Path
import hashlib,json,os
root=Path('/mnt/asus-root-stage')
for name in ('bin/busybox','usr/local/bin/asus-goodix-desktop','usr/local/bin/asus-goodix-browser','usr/local/bin/asus-dashboard.py','etc/machine-id','root/.mozilla/asus-appliance/prefs.js'):
 a=Path('/',name);b=root/name
 assert hashlib.sha256(a.read_bytes()).digest()==hashlib.sha256(b.read_bytes()).digest(),name
(root/'root/asus-os-persistence-check.txt').write_text('private SD Linux OS filesystem persistence v1\n')
os.sync()
run=Path('/run/asus-alpine');d=json.loads((run/'sd-root-build.json').read_text());d['phase']='POPULATED_AND_SELECTED_FILES_VERIFIED';(run/'sd-root-build.json').write_text(json.dumps(d)+'\n')
print('SD_OS_POPULATED_WITH_CLOSED_BROWSER_PROFILE; selected file hashes match')
PY
df -h "$T"
sync
