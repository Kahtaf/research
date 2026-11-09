set -eu
python3 /etc/asus-alpine/validate-wmt-loader.py /run/asus-alpine/wmt-loader.trace
python3 - <<'PY'
from pathlib import Path
import json,os,sqlite3,subprocess,time,urllib.request
mounts=[line.split() for line in Path('/proc/mounts').read_text().splitlines()]
root=[x for x in mounts if x[1]=='/' and x[2]=='ext4'];assert len(root)==1
assert root[0][0]=='/dev/asus-alpine-root-loop' and 'rw' in root[0][3].split(',')
assert Path('/run/asus-alpine/root-mode').read_text().strip()=='SD-loop'
loop=Path('/run/asus-alpine/root-loop-device').read_text().strip()
backing=Path('/sys/class/block',loop,'loop/backing_file').read_text().strip()
assert backing.endswith('/2026-11-08-asus-alpine/alpine-root.ext4'),backing
sd=[x for x in mounts if x[1]=='/mnt/alpine-sd'];assert len(sd)==1
assert {'rw','nosuid','nodev','noexec','fmask=0177','dmask=0077'}<=set(sd[0][3].split(','))
system=[x for x in mounts if x[1]=='/system'];assert len(system)==1 and 'ro' in system[0][3].split(',')
assert [x for x in mounts if x[1]=='/tmp'][0][2]=='tmpfs'
assert Path('/root/asus-os-persistence-check.txt').read_text()=='private SD Linux OS filesystem persistence v1\n'
assert Path('/root/.mozilla/asus-appliance/prefs.js').is_file()
wpa=subprocess.check_output(['wpa_cli','-iwlan0','status'],text=True)
assert 'wpa_state=COMPLETED\n' in wpa
p=Path('/run/asus-alpine/udhcpc.pid').read_text().strip()
args=Path('/proc',p,'cmdline').read_bytes().split(b'\0');assert args[0]==b'udhcpc' and b'wlan0' in args
health=json.load(urllib.request.urlopen('http://127.0.0.1:8080/health',timeout=5))
assert health['requests_saved']>11,health
assert b'microSD system' in urllib.request.urlopen('http://127.0.0.1:8080/',timeout=5).read()
assert os.path.samefile('/var/lib/asus-dashboard','/mnt/alpine-sd/2026-11-08-asus-alpine/service-data')
db=Path('/root/asus-service-proof.sqlite')
assert not db.exists()
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
with sqlite3.connect(db) as c:
 c.execute('CREATE TABLE proof (boot_id TEXT PRIMARY KEY, stamp REAL)')
 c.execute('INSERT INTO proof VALUES (?,?)',(boot,time.time()))
 assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
Path('/root/asus-first-sd-boot.txt').write_text(boot+'\n')
os.sync()
print(json.dumps({'root_mode':'SD-loop','root_filesystem':'ext4 rw','outer_card_protected':True,'stock_system_read_only':True,'wifi':'COMPLETED','resident_dhcp':True,'dashboard_saved_requests':health['requests_saved'],'browser_profile_retained':True,'os_sqlite_commit_read':'PASS'}))
PY
curl --fail --silent --show-error --max-time 20 https://alpinelinux.org/ --output /dev/null
echo STANDALONE_SD_HTTPS_PASS
export DISPLAY=:0 XAUTHORITY=/run/asus-goodix/Xauthority
xdotool search --onlyvisible --class firefox getwindowname
tail -5 /run/asus-goodix/browser-windows.txt
df -h / /tmp /dev/shm
