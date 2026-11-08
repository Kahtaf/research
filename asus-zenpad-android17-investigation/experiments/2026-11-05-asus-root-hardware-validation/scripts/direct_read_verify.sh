#!/system/bin/sh
set -eu
trap 'setenforce 1' EXIT
for item in boot:9 recovery:10 lk:8; do
    name=${item%:*}
    part=${item#*:}
    dd if=/dev/block/mmcblk0p$part of=/data/local/tmp/asus-$name-root.bin bs=1048576
    chmod 600 /data/local/tmp/asus-$name-root.bin
    chown 2000:2000 /data/local/tmp/asus-$name-root.bin
done
echo DIRECT_READS_COMPLETE
echo PHYSICAL_TOUCH_CAPTURE_START
# This is the real Goodix event node from getevent -lp; software injection does
# not supply physical touchscreen events here. No events is inconclusive.
timeout 20 getevent -lt /dev/input/event11 || { result=$?; [ "$result" = 124 ] || [ "$result" = 143 ]; }
echo PHYSICAL_TOUCH_CAPTURE_END
