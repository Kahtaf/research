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
name=alpine-3.24.4-ram-rootfs.tar.gz
[ ! -e "$D/$name" ]
cp /data/local/tmp/asus-alpine-rootfs.tar.gz "$D/$name.uploading"
expected=$(cut -d ' ' -f 1 /data/local/tmp/asus-alpine-rootfs.tar.gz.sha256)
actual=$(chroot "$R" /bin/busybox sha256sum < "$D/$name.uploading" | cut -d ' ' -f 1)
[ "$actual" = "$expected" ]
mv "$D/$name.uploading" "$D/$name"
cp /data/local/tmp/asus-alpine-rootfs.tar.gz.sha256 "$D/$name.sha256"
sync
printf 'SD_ROOTFS_SHA256_MATCH %s\n' "$actual"
ls -l "$D/$name"
# Remove only the incomplete archive created by our failed bounded gzip trial.
[ ! -f "$D/$name.partial" ] || rm "$D/$name.partial"
