/system/bin/wpa_cli -p /data/misc/wifi/sockets -iwlan0 list_networks
/system/bin/wpa_cli -p /data/misc/wifi/sockets -iwlan0 status
getprop wifi.supplicant_state
getprop dhcp.wlan0.result
dumpsys wifi > /data/local/tmp/asus-alpine-wifi-state.txt
chown shell:shell /data/local/tmp/asus-alpine-wifi-state.txt
chmod 600 /data/local/tmp/asus-alpine-wifi-state.txt
