R=/data/local/tmp/asus-alpine-ram
CARD=$(chroot "$R" /usr/bin/python3 - <<'PY'
from pathlib import Path
p=[line.split()[1] for line in Path('/proc/mounts').read_text().splitlines() if line.split()[0]=='/dev/block/vold/public:179,129' and line.split()[2]=='vfat' and line.split()[1].startswith('/mnt/media_rw/')]
assert len(p)==1,p
print(p[0])
PY
)
D=$CARD/2026-11-08-asus-alpine
[ "$(cat "$D/ALPINE.ID")" = asus-alpine-stock-kernel-v1 ]
[ "$(cat "$R/etc/asus-alpine-ram-release")" = asus-alpine-stock-kernel-v1 ]
name=alpine-3.24.4-ram-rootfs.tar.gz
[ ! -e "$D/$name" ]
[ ! -e "$D/$name.partial" ]
# Save software only. Radio profiles/calibration/auth keys remain separate private sidecars.
chroot "$R" /usr/bin/env -i PATH=/usr/sbin:/usr/bin:/sbin:/bin /usr/bin/timeout -k 2 48 /bin/tar -czf - \
 --exclude='./proc/*' --exclude='./sys/*' --exclude='./dev/*' \
 --exclude='./run/*' --exclude='./tmp/*' --exclude='./opt/android' \
 --exclude='./root/.ssh' --exclude='./etc/wpa*private*' --exclude='./etc/asus-standalone*' \
 --exclude='./etc/ssh/ssh_host*' --exclude='./var/log/*' --exclude='./var/lib/asus-dashboard/*' \
 -C / . > "$D/$name.partial"
sync
mv "$D/$name.partial" "$D/$name"
chroot "$R" /bin/busybox sha256sum < "$D/$name" | sed "s/  -$/  $name/" > "$D/$name.sha256"
cat "$D/$name.sha256"
ls -l "$D/$name"
