R=/data/local/tmp/asus-alpine-ram
ps | grep -E 'wpa_supplicant|wmt_launcher|sshd' || true
ip -4 addr show wlan0
ip route show table all
cat "$R/tmp/wpa-native.log" | tail -20
cat "$R/tmp/sshd.log"
getprop init.svc.p2p_supplicant
getprop wlan.driver.status
getprop dhcp.wlan0.ipaddress
chroot "$R" /usr/bin/curl -fsS --max-time 8 https://alpinelinux.org/ -o /tmp/post-restore-https.html
chroot "$R" /usr/bin/wc -c /tmp/post-restore-https.html
C=$R/opt/android
mkdir -p "$C/dev" "$C/tmp"
tar -xf /data/local/tmp/asus-alpine-stock-deps.tar -C "$C"
ln -s /system/vendor "$C/vendor"
# No WMT device nodes, /proc or network utilities are exposed in this subtree.
set +e
timeout 3 chroot "$C" /system/vendor/bin/wmt_launcher -h
rc=$?
echo "BIONIC_HELP_EXIT=$rc"
