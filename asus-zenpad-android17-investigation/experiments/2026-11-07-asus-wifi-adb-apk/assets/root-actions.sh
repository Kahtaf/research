#!/system/bin/sh
set -eu
trap '/system/bin/setenforce 1' EXIT HUP INT TERM
[ "$(id -u)" = 0 ]
[ "$(getprop ro.serialno)" = DEVICE_SERIAL_REDACTED ]
[ "$(getprop ro.product.device)" = P00A_2 ]
[ "$(getprop ro.adb.secure)" = 1 ]
setprop persist.adb.tcp.port 5555
setprop service.adb.tcp.port 5555
[ "$(getprop persist.adb.tcp.port)" = 5555 ]
[ "$(getprop service.adb.tcp.port)" = 5555 ]
setprop ctl.restart adbd
printf 'ASUS Wi-Fi ADB settings applied.\n'
