id
ps
ls -l /dev/*wmt* /dev/*stp* /dev/*wifi* /dev/conn* /dev/fb* /dev/graphics/* 2>/dev/null || true
cat /proc/modules
cat /proc/filesystems
cat /proc/partitions
cat /sys/class/graphics/fb0/virtual_size /sys/class/graphics/fb0/bits_per_pixel /sys/class/graphics/fb0/stride 2>/dev/null || true
ls -la /mnt/media_rw/FA06-080C
ls -l /init* /system/etc/*wmt* /system/bin/*wmt* /system/bin/*nvram* /system/etc/firmware 2>/dev/null || true
for p in /init*.rc; do echo "=== $p"; cat "$p"; done
getevent -lp /dev/input/event11
