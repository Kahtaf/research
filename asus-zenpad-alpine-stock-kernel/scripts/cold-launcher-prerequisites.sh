ls -l /dev/null /dev/zero /dev/random /dev/urandom /dev/stpwmt
ls -ld /system /system/bin /system/vendor /system/vendor/bin
cat /sys/power/autosleep 2>/dev/null
cat /proc/sys/kernel/random/boot_id
dmesg | tail -20
