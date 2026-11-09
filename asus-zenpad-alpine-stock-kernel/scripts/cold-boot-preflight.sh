R=/data/local/tmp/asus-alpine-ram
chroot "$R" /usr/bin/strace --kill-on-exit -X raw -e trace=ioctl -o /tmp/ioctl-format.trace /usr/bin/python3 - <<'PY'
import os,fcntl,errno
fd=os.open('/dev/null',os.O_RDONLY)
try:fcntl.ioctl(fd,0x80047704,0)
except OSError as e:
 assert e.errno==errno.ENOTTY
 print('HARMLESS_IOCTL_FORMAT_NEGATIVE_CONTROL_PASS')
else:raise AssertionError('Expected /dev/null ENOTTY')
PY
cat "$R/tmp/ioctl-format.trace"
for p in mmcblk0p9 mmcblk0p10 mmcblk0p12 mmcblk0p25; do
 echo "GEOMETRY $p"
 cat "/sys/class/block/$p/start" "/sys/class/block/$p/size" "/sys/class/block/$p/dev"
done
for node in wmtdetect stpwmt wmtWifi; do
 echo "NODE $node"
 for d in /sys/class/*/"$node"; do [ ! -r "$d/dev" ] || { echo "$d"; cat "$d/dev"; }; done
done
cat /sys/class/block/mmcblk1/device/type
cat /proc/sys/kernel/random/boot_id
dd if=/dev/block/platform/mtk-msdc.0/11230000.MSDC0/by-name/para of=/data/local/tmp/asus-alpine-bcb.preflight.bin bs=2048 count=1 2>/dev/null
chown shell:shell /data/local/tmp/asus-alpine-bcb.preflight.bin
chmod 600 /data/local/tmp/asus-alpine-bcb.preflight.bin
dd if=/dev/block/platform/mtk-msdc.0/11230000.MSDC0/by-name/boot bs=1048576 2>/dev/null | chroot "$R" /bin/busybox sha256sum
dd if=/dev/block/platform/mtk-msdc.0/11230000.MSDC0/by-name/recovery bs=1048576 2>/dev/null | chroot "$R" /bin/busybox sha256sum
