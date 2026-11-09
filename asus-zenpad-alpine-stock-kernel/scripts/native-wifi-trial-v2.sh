R=/data/local/tmp/asus-alpine-ram
[ "$(stat -f -c %T "$R")" = tmpfs ]
[ "$(getprop init.svc.p2p_supplicant)" = running ]
[ "$(readlink /proc/265/exe)" = /system/vendor/bin/wmt_launcher ]
cp /data/misc/wifi/wpa_supplicant.conf "$R/etc/wpa-stock-private.conf"
chmod 600 "$R/etc/wpa-stock-private.conf"
chroot "$R" /usr/bin/python3 - <<'PY'
import re
s=open('/etc/wpa-stock-private.conf').read()
blocks=re.findall(r'^network=\{\s*\n.*?^\}',s,re.M|re.S)
assert blocks, 'No stock station profiles; stop'
open('/etc/wpa-native-private.conf','w').write('ctrl_interface=/run/wpa_supplicant\nupdate_config=0\n'+ '\n'.join(blocks)+'\n')
PY
chmod 600 "$R/etc/wpa-native-private.conf"
cat > "$R/etc/asus-udhcpc" <<'DHCP'
#!/bin/sh
case "$1" in
bound|renew)
 /sbin/ifconfig "$interface" "$ip" netmask "$subnet" up
 for gw in $router; do /sbin/ip route add default via "$gw" dev "$interface" metric 42760; break; done
 : > /etc/resolv.conf
 for server in $dns; do echo "nameserver $server" >> /etc/resolv.conf; done
 echo NATIVE_DHCP_BOUND
;;
esac
DHCP
chmod 700 "$R/etc/asus-udhcpc"
restore_wifi() {
 set +e
 echo RESTORE_ANDROID_WIFI
 if [ -s "$R/run/wpa-native.pid" ]; then
   p=$(cat "$R/run/wpa-native.pid")
   [ "$(readlink /proc/$p/exe)" = "$R/sbin/wpa_supplicant" ] && kill "$p"
 fi
 chroot "$R" /sbin/ip route del default dev wlan0 metric 42760 2>/dev/null
 svc wifi enable
}
trap restore_wifi EXIT INT TERM
svc wifi disable
sleep 3
[ "$(getprop init.svc.p2p_supplicant)" = stopped ]
[ "$(getprop init.svc.wpa_supplicant)" != running ]
[ "$(readlink /proc/265/exe)" = /system/vendor/bin/wmt_launcher ]
printf 1 > /dev/wmtWifi
for n in 1 2 3 4 5; do [ -d /sys/class/net/wlan0 ] && break; sleep 1; done
[ -d /sys/class/net/wlan0 ]
chroot "$R" /sbin/wpa_supplicant -B -Dnl80211 -iwlan0 -c/etc/wpa-native-private.conf -P/run/wpa-native.pid > "$R/tmp/wpa-native.log" 2>&1
for n in 1 2 3 4 5 6 7 8 9 10; do
 if chroot "$R" /sbin/wpa_cli -iwlan0 status | grep -q '^wpa_state=COMPLETED'; then break; fi
 sleep 1
done
chroot "$R" /sbin/wpa_cli -iwlan0 status
chroot "$R" /sbin/wpa_cli -iwlan0 status | grep -q '^wpa_state=COMPLETED'
chroot "$R" /sbin/udhcpc -n -q -t 3 -T 3 -i wlan0 -s /etc/asus-udhcpc
chroot "$R" /usr/bin/curl -fsS --max-time 10 https://alpinelinux.org/ -o /tmp/native-wifi-https.html
chroot "$R" /usr/bin/wc -c /tmp/native-wifi-https.html
echo NATIVE_ALPINE_WIFI_ASSOC_DHCP_TLS_PASS
