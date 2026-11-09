set -eu
python3 /etc/asus-alpine/validate-wmt-loader.py /run/asus-alpine/wmt-loader.trace
python3 - <<'PY'
from pathlib import Path
import json,os,sqlite3,urllib.request
first=Path('/root/asus-first-sd-boot.txt').read_text().strip()
current=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
assert first!=current
assert Path('/root/asus-os-persistence-check.txt').read_text()=='private SD Linux OS filesystem persistence v1\n'
with sqlite3.connect('/root/asus-service-proof.sqlite') as c:
 assert c.execute('SELECT boot_id FROM proof').fetchall()==[(first,)]
 assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
health=json.load(urllib.request.urlopen('http://127.0.0.1:8080/health',timeout=5))
assert health['requests_saved']>=15
profile=Path('/root/.mozilla/asus-appliance')
assert (profile/'prefs.js').is_file() and (profile/'places.sqlite').is_file()
p=Path('/run/asus-alpine/udhcpc.pid').read_text().strip()
assert Path('/proc',p,'cmdline').read_bytes().split(b'\0')[0]==b'udhcpc'
mounts=[x.split() for x in Path('/proc/mounts').read_text().splitlines()]
assert len([x for x in mounts if x[1]=='/' and x[2]=='ext4' and 'rw' in x[3].split(',')])==1
assert 'tmpfs'==[x[2] for x in mounts if x[1]=='/tmp'][0]
print(json.dumps({'os_file_survived_reboot':True,'os_sqlite_transaction_survived':True,'os_sqlite_integrity':'ok','dashboard_saved_requests':health['requests_saved'],'browser_profile_files_retained':True,'browser_history_integrity':'check after closing live Firefox','resident_dhcp_alive':True}))
PY
wpa_cli -iwlan0 status | grep '^wpa_state=COMPLETED$'
curl --fail --silent --show-error --max-time 20 https://alpinelinux.org/ --output /dev/null
echo REBOOTED_SD_HTTPS_PASS
export DISPLAY=:0 XAUTHORITY=/run/asus-goodix/Xauthority
xdotool search --onlyvisible --class firefox getwindowname
df -h / /tmp
