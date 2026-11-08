#!/data/data/com.termux/files/usr/bin/bash
set -eu
umask 077
base=http://LAN_ADDRESS_REDACTED:8765
work=$(mktemp -d "$HOME/asus-wifi.XXXXXXXX")
cd "$work"
[ "$(/system/bin/getprop ro.serialno)" = DEVICE_SERIAL_REDACTED ]
[ "$(/system/bin/getprop ro.product.device)" = P00A_2 ]
[ "$(/system/bin/getprop ro.build.version.sdk)" = 24 ]
[ "$(/system/bin/getprop ro.build.fingerprint)" = 'asus/WW_P00A/P00A_2:7.0/NRD90M/WW_P00A-V5.3.20-20180809:user/release-keys' ]
[ "$(/system/bin/getprop ro.adb.secure)" = 1 ]
[ "$(/system/bin/getenforce)" = Enforcing ]
curl --fail --connect-timeout 10 --max-time 60 "$base/mtk-su64" -o mtk-su64
curl --fail --connect-timeout 10 --max-time 30 "$base/root-actions.sh" -o root-actions.sh
printf '%s\n' '328632e853ff6427af9f35cb83a91d9e960f35d01188ee66d46ae9c7ce7c7827  mtk-su64' | sha256sum -c -
printf '%s\n' '75bc4f393a44c8dfb4663b8da53e7986e1dca47ddf6b0c18472f39b2c523e05b  root-actions.sh' | sha256sum -c -
chmod 700 mtk-su64
printf '\nEnabling authenticated Wi-Fi ADB on this ASUS only...\n'
unset LD_PRELOAD LD_LIBRARY_PATH
PATH=/system/bin:/system/xbin
export PATH
./mtk-su64 -c /system/bin/sh < root-actions.sh
[ "$(/system/bin/getenforce)" = Enforcing ]
[ "$(/system/bin/getprop persist.adb.tcp.port)" = 5555 ]
[ "$(/system/bin/getprop ro.adb.secure)" = 1 ]
printf '\nWi-Fi ADB configured. Accept the Mac debugging prompt when it appears.\n'
/system/bin/ip -f inet addr show wlan0
