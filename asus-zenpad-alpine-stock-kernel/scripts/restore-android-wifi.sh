svc wifi disable
sleep 3
svc wifi enable
sleep 8
getprop init.svc.p2p_supplicant
getprop wlan.driver.status
ip -4 addr show wlan0
ip route show table all
/system/bin/wpa_cli -p /data/misc/wifi/sockets -iwlan0 status 2>/dev/null || true
R=/data/local/tmp/asus-alpine-ram
chroot "$R" /usr/bin/curl -fsS --max-time 8 https://alpinelinux.org/ -o /tmp/restored-android-https.html
chroot "$R" /usr/bin/wc -c /tmp/restored-android-https.html
