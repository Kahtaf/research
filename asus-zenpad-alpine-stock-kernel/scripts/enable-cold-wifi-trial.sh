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
[ -f "$D/alpine-3.24.4-ram-rootfs.tar.gz.sha256" ]
[ "$(cut -d ' ' -f 1 "$D/alpine-3.24.4-ram-rootfs.tar.gz.sha256")" = b66439ef6641e7e1b0649c78c6308d1a3daa1393dd25f1fe47bfba0f8100934e ]
for name in WIFI WIFI_CUSTOM; do
 before=$(chroot "$R" /bin/busybox sha256sum < "/data/nvram/APCFG/APRDEB/$name" | cut -d ' ' -f 1)
 after=$(chroot "$R" /bin/busybox sha256sum < "$D/private/$name" | cut -d ' ' -f 1)
 [ "$before" = "$after" ]
done
[ -s "$D/private/wpa_supplicant.conf" ]
[ -s "$D/private/authorized_keys" ]
[ ! -e "$D/COLD-WIFI.ENABLE" ]
printf 'asus-alpine-stock-wmt-v1\n' > "$D/COLD-WIFI.ENABLE"
sync
echo COLD_WIFI_SD_TRIAL_READY_ORIGINAL_CALIBRATION_MATCHES
