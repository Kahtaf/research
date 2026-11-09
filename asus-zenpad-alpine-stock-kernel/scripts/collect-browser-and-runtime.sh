R=/data/local/tmp/asus-alpine-ram
mkdir -p /data/local/tmp/asus-alpine-browser-result
cp "$R/run/asus-goodix/"* /data/local/tmp/asus-alpine-browser-result/ 2>/dev/null || true
cp "$R/tmp/dashboard-server.log" /data/local/tmp/asus-alpine-browser-result/
chown -R shell:shell /data/local/tmp/asus-alpine-browser-result
chmod -R u+rwX,go-rwx /data/local/tmp/asus-alpine-browser-result
C=$R/opt/android
mkdir "$C/proc"
mount -t proc proc "$C/proc"
set +e
chroot "$R" /usr/bin/timeout 3 /usr/bin/strace -f -o /tmp/bionic-with-proc.trace /usr/sbin/chroot /opt/android /system/vendor/bin/wmt_launcher -h
echo "BIONIC_PROC_EXIT=$?"
tail -25 "$R/tmp/bionic-with-proc.trace"
getprop init.svc.surfaceflinger
getprop init.svc.zygote
getprop init.svc.zygote_secondary
