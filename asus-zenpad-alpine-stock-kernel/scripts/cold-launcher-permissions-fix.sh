[ -f /run/asus-alpine/wmt-loader.started ] || exit 41
python3 /etc/asus-alpine/validate-wmt-loader.py /run/asus-alpine/wmt-loader.trace || exit 42
old=$(cat /run/asus-alpine/wmt-launcher.pid)
[ ! -e /proc/$old ] || { echo ORIGINAL_LAUNCHER_STILL_PRESENT; exit 43; }
chmod 666 /dev/null /dev/zero /dev/random /dev/urandom /dev/tty /dev/ptmx
ip link set lo up
/bin/busybox su -s /bin/sh asus-wmt -c 'exec /vendor/bin/wmt_launcher -p /vendor/firmware/' > /run/asus-alpine/wmt-launcher.log 2>&1 &
p=$!
echo "$p" > /run/asus-alpine/wmt-launcher.pid
sleep 1
[ "$(readlink /proc/$p/exe)" = /system/vendor/bin/wmt_launcher ] || { echo LAUNCHER_START_FAILED; exit 44; }
echo WMT_LAUNCHER_ALIVE
cat /proc/$p/wchan
timeout -k 2 15 sh -c 'printf 1 > /dev/wmtWifi'
echo WIFI_POWER_EXIT=$?
ip link show wlan0
dmesg | grep -Ei 'wmt|stp|wlan|firmware|consys|wifi' | tail -35
