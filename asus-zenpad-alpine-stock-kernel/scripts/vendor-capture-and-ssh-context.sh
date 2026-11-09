R=/data/local/tmp/asus-alpine-ram
id -Z
ls -Zd "$R" "$R/usr/lib/ssh/sshd-session" "$R/usr/sbin/sshd" "$R/lib/ld-musl-aarch64.so.1"
dmesg | grep 'avc:.*denied' | tail -15 || true
cat /proc/265/cmdline
ls -l /proc/265/fd
# Private stock dependencies are captured without publishing or modifying them.
tar -cf /data/local/tmp/asus-alpine-stock-deps.tar /system/vendor/bin/wmt_loader /system/vendor/bin/wmt_launcher /system/bin/linker64 /system/lib64/libc.so /system/lib64/libcutils.so /system/lib64/libc++.so /system/lib64/libm.so /system/lib64/liblog.so /system/lib64/libdl.so /system/vendor/firmware /data/nvram/APCFG/APRDEB/WIFI /data/nvram/APCFG/APRDEB/WIFI_CUSTOM
chown shell:shell /data/local/tmp/asus-alpine-stock-deps.tar
chmod 600 /data/local/tmp/asus-alpine-stock-deps.tar
chroot "$R" /sbin/wpa_supplicant -v
