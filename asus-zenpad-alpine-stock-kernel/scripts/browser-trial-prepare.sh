R=/data/local/tmp/asus-alpine-ram
cp /data/local/tmp/asus-goodix-bin/asus-goodix-desktop "$R/usr/local/bin/"
cp /data/local/tmp/asus-dashboard.py "$R/usr/local/bin/"
chmod 755 "$R/usr/local/bin/asus-goodix-desktop"
chroot "$R" /usr/bin/env -i PATH=/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin /bin/sh -c 'command -v netsurf; tail -20 /tmp/sshd-bounded.log; command -v chroot; command -v strace'
cat "$R/run/asus-goodix/Xorg.log" | tail -25
# Trace the isolated stock runtime without any WMT node or proc mount.
set +e
chroot "$R" /usr/bin/strace -f -o /tmp/bionic-launcher.trace /usr/sbin/chroot /opt/android /system/vendor/bin/wmt_launcher -h
echo "BIONIC_TRACE_EXIT=$?"
tail -30 "$R/tmp/bionic-launcher.trace"
