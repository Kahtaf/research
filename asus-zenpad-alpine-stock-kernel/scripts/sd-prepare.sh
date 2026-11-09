R=/data/local/tmp/asus-alpine-ram
CARD=$(chroot "$R" /usr/bin/python3 - <<'PY'
from pathlib import Path
p=[line.split()[1] for line in Path('/proc/mounts').read_text().splitlines() if line.split()[0]=='/dev/block/vold/public:179,129' and line.split()[2]=='vfat' and line.split()[1].startswith('/mnt/media_rw/')]
assert len(p)==1,p
print(p[0])
PY
)
[ ! -L "$CARD" ]
[ -b /dev/block/vold/public:179,129 ]
[ "$(stat -c %t:%T /dev/block/vold/public:179,129)" = "$(stat -c %t:%T /dev/block/mmcblk1p1)" ]
D=$CARD/2026-11-08-asus-alpine
[ ! -e "$D" ]
mkdir "$D" "$D/service-data" "$D/private"
printf 'asus-alpine-stock-kernel-v1\n' > "$D/ALPINE.ID"
printf 'RAM Alpine experiment inputs and service data. Not an Android installer. No old rescue trigger is consumed. Private radio calibration and station configuration stay local.\n' > "$D/README.txt"
cp "$R/var/lib/asus-dashboard/status.sqlite" "$D/service-data/status.sqlite"
# Preserve exact private calibration files, never regenerate them.
cp /data/nvram/APCFG/APRDEB/WIFI "$D/private/WIFI"
cp /data/nvram/APCFG/APRDEB/WIFI_CUSTOM "$D/private/WIFI_CUSTOM"
cp /data/local/tmp/asus-alpine-trial-key.pub "$D/private/authorized_keys"
# Stage a single connected profile, without printing credentials.
id=$(/system/bin/wpa_cli -p /data/misc/wifi/sockets -iwlan0 status | sed -n 's/^id=//p')
[ -n "$id" ]
/system/bin/wpa_cli -p /data/misc/wifi/sockets -iwlan0 get_network "$id" ssid > "$R/tmp/active-ssid-private"
chroot "$R" /usr/bin/python3 - <<'PY'
import re
s=open('/etc/wpa-native-private.conf').read(); ssid=open('/tmp/active-ssid-private').read().strip()
blocks=re.findall(r'^network=\{\s*\n.*?^\}',s,re.M|re.S)
chosen=[b for b in blocks if (m:=re.search(r'^\s*ssid\s*=\s*(.*)$',b,re.M)) and m[1].strip()==ssid]
assert len(chosen)==1,len(chosen)
open('/etc/asus-standalone-wpa-private.conf','w').write('ctrl_interface=/run/wpa_supplicant\nupdate_config=0\np2p_disabled=1\n'+chosen[0]+'\n')
PY
cp "$R/etc/asus-standalone-wpa-private.conf" "$D/private/wpa_supplicant.conf"
# Bind only the new service data directory; verify the actual backing device.
mount -o bind "$D/service-data" "$R/var/lib/asus-dashboard"
[ "$(stat -c %d "$R/var/lib/asus-dashboard")" = "$(stat -c %d "$D/service-data")" ]
chroot "$R" /usr/bin/python3 - <<'PY'
import sqlite3,os
p='/var/lib/asus-dashboard/status.sqlite'
with sqlite3.connect(p) as c:
 n=c.execute('select count(*) from visits').fetchone()[0]
 c.execute('create table if not exists persistence_check(value text)')
 c.execute('insert into persistence_check values (?)',('stock-kernel-sd-pass',))
print('SD_SQLITE_WRITE_PASS',n,os.stat(p).st_dev)
PY
sync
chroot "$R" /usr/bin/python3 - <<'PY'
import sqlite3
with sqlite3.connect('/var/lib/asus-dashboard/status.sqlite') as c:
 assert c.execute('select value from persistence_check order by rowid desc limit 1').fetchone()==('stock-kernel-sd-pass',)
print('SD_SQLITE_NEW_PROCESS_READ_PASS')
PY
cp "$R/tmp/bionic-with-proc.trace" /data/local/tmp/asus-alpine-bionic-trace.txt
chown shell:shell /data/local/tmp/asus-alpine-bionic-trace.txt
chmod 600 /data/local/tmp/asus-alpine-bionic-trace.txt
df -h "$D"

printf 'asus-alpine-stock-kernel-v1\n' > "$R/etc/asus-alpine-ram-release"
dd if=/dev/block/platform/mtk-msdc.0/11230000.MSDC0/by-name/para of=/data/local/tmp/asus-alpine-bcb.before.bin bs=2048 count=1 2>/dev/null
chown shell:shell /data/local/tmp/asus-alpine-bcb.before.bin
chmod 600 /data/local/tmp/asus-alpine-bcb.before.bin
dd if=/dev/block/platform/mtk-msdc.0/11230000.MSDC0/by-name/boot bs=1048576 2>/dev/null | chroot "$R" /bin/busybox sha256sum
dd if=/dev/block/platform/mtk-msdc.0/11230000.MSDC0/by-name/recovery bs=1048576 2>/dev/null | chroot "$R" /bin/busybox sha256sum
