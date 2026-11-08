#!/system/bin/sh
# Read-only hardware/block diagnostics. Writes only private scratch backups.
set -eu
trap 'setenforce 1' EXIT
[ "$(id -u)" = 0 ] || exit 93
echo ROOT_IDENTITY
id
echo BLOCK_LAYOUT
ls -l /dev/block/mmcblk0 /dev/block/mmcblk0boot0 /dev/block/mmcblk0boot1
ls -l /dev/block/platform/*/by-name /dev/block/platform/*/*/by-name 2>/dev/null || true
echo POWER_SUPPLIES
for supply in /sys/class/power_supply/*; do
    echo "$supply"
    cat "$supply/uevent" || true
done
echo INPUT_CAPABILITIES
getevent -lp
echo GPT_BACKUP
sectors=$(cat /sys/class/block/mmcblk0/size)
case "$sectors" in ''|*[!0-9]*) exit 94 ;; esac
[ "$sectors" -gt 1000000 ] && [ "$sectors" -lt 1000000000 ] || exit 95
dd if=/dev/block/mmcblk0 of=/data/local/tmp/asus-primary-gpt.bin bs=512 count=34
dd if=/dev/block/mmcblk0 of=/data/local/tmp/asus-backup-gpt.bin bs=512 skip=$((sectors - 33)) count=33
chmod 600 /data/local/tmp/asus-primary-gpt.bin /data/local/tmp/asus-backup-gpt.bin
chown 2000:2000 /data/local/tmp/asus-primary-gpt.bin /data/local/tmp/asus-backup-gpt.bin
# Android 7's toybox lacks sha256sum; the pulled files are hashed on the Mac.
echo ROOT_BASELINE_COMPLETE
