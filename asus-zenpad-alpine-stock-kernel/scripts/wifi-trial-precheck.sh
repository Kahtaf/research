R=/data/local/tmp/asus-alpine-ram
cat "$R/tmp/sshd.log"
ls -l /data/misc/wifi/wpa_supplicant.conf
getprop init.svc.wpa_supplicant
getprop init.svc.p2p_supplicant
getprop wlan.driver.status
getprop wifi.interface
ls -l /sys/class/net/wlan0
chroot "$R" /usr/sbin/iw dev
chroot "$R" /usr/sbin/wpa_supplicant -v
ls -l /proc/265/fd
