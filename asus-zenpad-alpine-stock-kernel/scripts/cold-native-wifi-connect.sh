[ -d /sys/class/net/wlan0 ] || exit 51
[ ! -e /run/asus-alpine/wpa.pid ] || exit 52
timeout -k 2 10 wpa_supplicant -B -Dnl80211 -iwlan0 -c/etc/asus-alpine/wpa_supplicant.conf -P/run/asus-alpine/wpa.pid > /run/asus-alpine/wpa.log 2>&1 || { tail -15 /run/asus-alpine/wpa.log; exit 53; }
for attempt in 1 2 3 4 5 6 7 8 9 10; do
 wpa_cli -iwlan0 status | grep -q '^wpa_state=COMPLETED' && break
 sleep 1
done
wpa_cli -iwlan0 status | grep '^wpa_state='
wpa_cli -iwlan0 status | grep -q '^wpa_state=COMPLETED' || exit 54
timeout -k 2 20 udhcpc -n -q -t 3 -T 4 -i wlan0 -s /etc/asus-alpine/udhcpc || exit 55
curl -fsS --max-time 8 https://alpinelinux.org/ -o /tmp/standalone-wifi-https.html || exit 56
wc -c /tmp/standalone-wifi-https.html
echo STANDALONE_WIFI_ASSOC_DHCP_TLS_PASS
printf 'ALPINE_WLAN_IPV4='
ip -o -4 addr show wlan0 | awk '{print $4}' | cut -d/ -f1
printf 'ALPINE_HOST_KEY='
cat /etc/ssh/ssh_host_ed25519_key.pub
