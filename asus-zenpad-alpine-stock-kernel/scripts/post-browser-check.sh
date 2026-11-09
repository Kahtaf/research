sleep 10
R=/data/local/tmp/asus-alpine-ram
ps | grep -E 'wmt_launcher|strace|sshd|netsurf|Xorg|asus-mtk' || true
getprop init.svc.surfaceflinger
getprop init.svc.zygote
getprop init.svc.zygote_secondary
/system/bin/wpa_cli -p /data/misc/wifi/sockets -iwlan0 status
chroot "$R" /usr/bin/curl -fsS --max-time 8 https://alpinelinux.org/ -o /tmp/post-browser-https.html
chroot "$R" /usr/bin/wc -c /tmp/post-browser-https.html
tail -40 "$R/tmp/bionic-with-proc.trace"
ls -l /dev/block/platform/mtk-msdc.0/11230000.MSDC0/by-name
ls -l /sys/class/block/loop*/dev 2>/dev/null || true
