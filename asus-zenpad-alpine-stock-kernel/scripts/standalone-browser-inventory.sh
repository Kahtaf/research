set -eu
apk search -x firefox firefox-esr chromium
apk add --simulate firefox-esr
cat /proc/meminfo | head -4
df -h /
ls -l /dev/fb0 /dev/graphics/fb0 /dev/uinput 2>/dev/null || true
