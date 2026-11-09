sleep 12
/system/bin/wpa_cli -p /data/misc/wifi/sockets -iwlan0 status
getprop dhcp.wlan0.ipaddress
R=/data/local/tmp/asus-alpine-ram
chroot "$R" /usr/bin/curl -fsS --max-time 8 https://alpinelinux.org/ -o /tmp/awake-restored-https.html
chroot "$R" /usr/bin/wc -c /tmp/awake-restored-https.html
