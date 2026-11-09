set -eu
cat /run/asus-alpine/root-mode
apk add --simulate xf86-input-libinput libinput-tools eudev
apk add --no-cache xf86-input-libinput libinput-tools eudev
command -v udevadm
command -v libinput
python3 /usr/local/bin/goodix-preflight.py
df -h /
